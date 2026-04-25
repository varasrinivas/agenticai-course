#!/bin/bash
# build-course.sh — Master build script with rate limit handling + resume
# Usage: ./build-course.sh [setup|generate|fix|capstones|labs|finalize|all] [--resume]

set -e
PHASE=${1:-all}
RESUME=${2:-""}
PROJECT_DIR=$(pwd)
LOG_DIR="${PROJECT_DIR}/build-logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/build_${TIMESTAMP}.log"
PROGRESS_FILE="${LOG_DIR}/progress.json"
MAX_RETRIES=5
INITIAL_WAIT=60
MAX_WAIT=3600
DAILY_LIMIT_WAIT=14400  # 4 hours

mkdir -p "$LOG_DIR" output

log() { echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

load_completed() { [ -f "$PROGRESS_FILE" ] && cat "$PROGRESS_FILE" || echo '{"completed":[],"calls":0,"retries":0}'; }

is_completed() { load_completed | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if '$1' in d.get('completed',[]) else 1)" 2>/dev/null; }

mark_completed() {
    local prog=$(load_completed)
    echo "$prog" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if '$1' not in d.get('completed',[]):
    d.setdefault('completed',[]).append('$1')
d['calls']=d.get('calls',0)+1
json.dump(d,open('$PROGRESS_FILE','w'),indent=2)
" 2>/dev/null
}

mark_retry() {
    local prog=$(load_completed)
    echo "$prog" | python3 -c "
import sys,json; d=json.load(sys.stdin); d['retries']=d.get('retries',0)+1
json.dump(d,open('$PROGRESS_FILE','w'),indent=2)
" 2>/dev/null
}

is_rate_limited() { echo "$1" | grep -qiE "rate.?limit|429|too many requests|quota exceeded|overloaded|usage limit|capacity"; }

is_daily_limited() { echo "$1" | grep -qiE "daily.?limit|daily.?quota|limit.*reset|come back|hours.*remaining"; }

wait_countdown() {
    local secs=$1 reason=$2
    local end=$(($(date +%s) + secs))
    log "⏳ $reason — waiting $secs seconds (until $(date -d "@$end" '+%H:%M:%S' 2>/dev/null || date -r $end '+%H:%M:%S' 2>/dev/null || echo 'soon'))"
    while [ $(date +%s) -lt $end ]; do
        local rem=$(( end - $(date +%s) ))
        printf "\r  Resuming in %d seconds...  " $rem
        sleep 5
    done
    printf "\r  Resuming now.              \n"
}

run_claude() {
    local desc="$1" cmd="$2" task_id="$3"
    
    if [ -n "$task_id" ] && is_completed "$task_id"; then
        log "⏭ SKIP (done): $desc"
        return 0
    fi
    
    log "▶ $desc"
    local retry=0 wait=$INITIAL_WAIT
    
    while [ $retry -le $MAX_RETRIES ]; do
        local output
        output=$(claude --dangerously-skip-permissions -p "$cmd" 2>&1) || true
        
        if is_daily_limited "$output"; then
            log "🛑 DAILY LIMIT — pausing ${DAILY_LIMIT_WAIT}s. Ctrl+C then: ./build-course.sh $PHASE --resume"
            mark_retry
            wait_countdown $DAILY_LIMIT_WAIT "Daily limit reached"
            retry=$((retry + 1))
            continue
        fi
        
        if is_rate_limited "$output"; then
            retry=$((retry + 1))
            mark_retry
            if [ $retry -gt $MAX_RETRIES ]; then
                log "✗ FAILED after $MAX_RETRIES retries: $desc"
                log "  Run: ./build-course.sh $PHASE --resume"
                exit 1
            fi
            wait_countdown $wait "Rate limited ($retry/$MAX_RETRIES)"
            wait=$((wait * 2 > MAX_WAIT ? MAX_WAIT : wait * 2))
            continue
        fi
        
        echo "$output" >> "$LOG_FILE"
        echo "$output" | head -15
        local lines=$(echo "$output" | wc -l)
        [ $lines -gt 15 ] && echo "  ...($((lines - 15)) more lines in log)"
        
        log "✓ $desc"
        [ -n "$task_id" ] && mark_completed "$task_id"
        return 0
    done
}

phase_setup() {
    log "=== SETUP ==="
    for f in CLAUDE.md .claude/commands/generate-module.md .claude/commands/fix-explanations.md prompts/07-depth-rules.md prompts/08-capstone-animations.md; do
        [ ! -f "$f" ] && { log "MISSING: $f"; exit 1; }
    done
    [ "$RESUME" = "--resume" ] && {
        local done=$(load_completed | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('completed',[])))" 2>/dev/null || echo 0)
        log "Resuming — $done tasks completed previously"
    }
    log "✓ $(ls output/M*.html 2>/dev/null | wc -l) modules in output/"
}

phase_generate() {
    log "=== GENERATE ==="
    for spec in "M00|gen-M00|Read all prompt files then generate module M00. Follow prompts/modules/M00-course-overview-agent-lifecycle.md. Include all 8 sections, 7 animations. Save to output/. Run quality checklist." \
                "M15B|gen-M15B|Read all prompt files then generate module M15B. Follow prompts/modules/M15B-build-complete-agent-system.md. 80% lab — every step: code, run command, expected output, checkpoint, troubleshooting. Save to output/." \
                "M22B|gen-M22B|Read all prompt files then generate module M22B. Follow prompts/modules/M22B-deploy-agent-gcp-aws-local.md. 3 tiers: Docker, GCP, AWS. Save to output/."; do
        IFS='|' read -r mod tid cmd <<< "$spec"
        [ -f output/${mod}*.html ] 2>/dev/null && { log "⏭ $mod exists"; continue; }
        run_claude "Generate $mod" "$cmd" "$tid"
        run_claude "Review $mod" "Review output/${mod}*.html against quality standards. Auto-fix critical issues." "review-$mod"
        run_claude "Compact" "/compact" ""
    done
}

phase_fix() {
    log "=== FIX ==="
    local bn=0
    for batch in "M00 M01 M02" "M03 M04 M05" "M06 M07 M08" "M09 M10 M11" "M12 M13 M14" "M15 M15B M16" "M17 M18 M19" "M20 M21 M22" "M22B M23 M24" "M25 M26 M27"; do
        bn=$((bn+1)); log "Batch $bn/10: $batch"
        for m in $batch; do
            ls output/${m}*.html >/dev/null 2>&1 || { log "⏭ $m — no file"; continue; }
            run_claude "Fix $m" "Apply all 8 fix-explanations passes to module $m in output/. Read prompts/07-depth-rules.md (14 rules), prompts/06-cert-tip-callouts.md. Pass 1-5 (explanations), Pass 6 (cert tips), Pass 7 (lab steps), Pass 8 (progress 'of 30'). str_replace only. Report word count." "fix-$m"
        done
        run_claude "Compact" "/compact" ""
    done
    run_claude "Consistency" "Scan all HTML in output/. Check CSS, fonts, nav, quizzes, progress bars. Report and auto-fix critical." "fix-consistency"
}

phase_capstones() {
    log "=== CAPSTONES ==="
    for spec in "CAPSTONE-1 DOMAIN-C|cap-1|CAPSTONE-1" "CAPSTONE-2 DOMAIN-C|cap-2|CAPSTONE-2" "CAPSTONE-3 DOMAIN-C|cap-3|CAPSTONE-3" "CAPSTONE-4 DOMAIN-C|cap-4|CAPSTONE-4" "CAPSTONE-5 DOMAIN-C|cap-5|CAPSTONE-5" "CAPSTONE-6|cap-6|CAPSTONE-6"; do
        IFS='|' read -r args tid file <<< "$spec"
        ls output/${file}*.html >/dev/null 2>&1 && { log "⏭ $file exists"; continue; }
        run_claude "Generate $args" "Read all prompt files including prompts/08-capstone-animations.md, prompts/03-capstone-domains.md. Read capstone brief if exists. Generate HTML for $args. Include architecture diagram, animations, lab steps (Rule 13), mock data, Tier 1 local deployment. Save to output/." "$tid"
        run_claude "Validate $file" "Validate output/${file}*.html. Run 10 passes. Auto-fix critical." "val-$file"
        run_claude "Compact" "/compact" ""
    done
}

phase_labs() {
    log "=== LABS ==="
    local bn=0
    for cmd in \
        "Generate lab repo for M00-M05 in labs/. Each: README.md, starter/, solution/ (Python+Node.js), expected_output/." \
        "Generate lab repo for M06-M11 in labs/. Include docs/ for M09." \
        "Generate lab repo for M12-M15, M15B in labs/. M15B: mock_data, tools, agents, tests." \
        "Generate lab repo for M16-M22, M22B in labs/. M22B: Dockerfile, docker-compose, deploy scripts." \
        "Generate lab repo for M25-M27 in labs/. M25: .claude/ structure. M27: mock exams." \
        "Generate lab repo for capstone-1 through capstone-3 in labs/ with domain-a/b/c." \
        "Generate lab repo for capstone-4 through capstone-6 in labs/. Capstone-6: 15 source files, bronze mock." \
        "Generate labs/README.md, SETUP.md, requirements.txt, package.json, .gitignore, .env.example, shared/."
    do
        bn=$((bn+1))
        run_claude "Labs $bn/8" "$cmd" "labs-$bn"
        run_claude "Compact" "/compact" ""
    done
}

phase_finalize() {
    log "=== FINALIZE ==="
    run_claude "Build index" "Scan output/ for all HTML. Generate output/index.html with 9 tracks, module cards, 3 learning paths." "fin-index"
    run_claude "Final check" "Scan ALL HTML in output/. Verify 'of 30', nav links, CSS, quizzes, cert tips, lab steps. Report inconsistencies." "fin-check"
    log "=== COMPLETE: $(ls output/M*.html 2>/dev/null | wc -l) modules, $(ls output/CAPSTONE*.html 2>/dev/null | wc -l) capstones ==="
    log "Preview: npx serve output -p 3000"
}

phase_mobile() {
    log "=== MOBILE ==="
    mkdir -p output/mobile
    local bn=0
    for batch in "M00, M01, M02, M03, M04, M05" "M06, M07, M08, M09, M10, M11" "M12, M13, M14, M15, M15B, M16" "M17, M18, M19, M20, M21, M22" "M22B, M23, M24, M25, M26, M27"; do
        bn=$((bn+1))
        run_claude "Mobile batch $bn/5: $batch" "Read prompts/09-mobile-design.md for mobile spec. For each module in $batch: read desktop HTML from output/, extract core concept, best analogy, convert code to pseudocode (10-15 lines, language-agnostic), take 2-3 misconceptions and 3 quiz questions. Generate 9-card mobile HTML with swipe nav. Save to output/mobile/{MODULE}-mobile.html. 800-1200 words. No real code. 16px font. 44px tap targets." "mobile-$bn"
        run_claude "Compact" "/compact" ""
    done
    run_claude "Mobile index" "Generate output/mobile/index.html as mobile course landing page with all modules as tap-friendly cards." "mobile-index"
    log "Mobile: $(ls output/mobile/*-mobile.html 2>/dev/null | wc -l) modules generated"
}

log "=== BUILD: Phase=$PHASE Resume=$RESUME Started=$(date) ==="
case $PHASE in
    setup) phase_setup;;
    generate) phase_setup; phase_generate;;
    fix) phase_setup; phase_fix;;
    capstones) phase_setup; phase_capstones;;
    labs) phase_setup; phase_labs;;
    mobile) phase_setup; phase_mobile;;
    finalize) phase_setup; phase_finalize;;
    all) phase_setup; phase_generate; phase_fix; phase_capstones; phase_labs; phase_mobile; phase_finalize;;
    *) echo "Usage: ./build-course.sh [setup|generate|fix|capstones|labs|mobile|finalize|all] [--resume]"; exit 1;;
esac
log "=== END: $(date) ==="
