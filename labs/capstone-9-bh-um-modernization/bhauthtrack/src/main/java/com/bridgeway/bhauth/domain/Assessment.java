package com.bridgeway.bhauth.domain;

import java.util.Date;

/**
 * A standardised instrument score. Maps onto BH_ASSESSMENT.
 *
 * <p>Four instruments share one table, distinguished by {@code instrument}:</p>
 *
 * <table border="1">
 *   <tr><th>instrument</th><th>dimension</th><th>score range</th><th>meaning</th></tr>
 *   <tr><td>{@code ASAM_DIM}</td><td>1..6</td><td>0..4</td>
 *       <td>ASAM multidimensional assessment. One row per dimension.</td></tr>
 *   <tr><td>{@code PHQ9}</td><td>null</td><td>0..27</td><td>Depression severity</td></tr>
 *   <tr><td>{@code GAD7}</td><td>null</td><td>0..21</td><td>Anxiety severity</td></tr>
 *   <tr><td>{@code CSSRS}</td><td>null</td><td>0..5</td>
 *       <td>Columbia suicide-severity rating. 4 and 5 are active ideation with intent.</td></tr>
 * </table>
 *
 * <p>The six ASAM dimensions, because the numbers appear bare in {@code PKG_LOC_RULES} and
 * nowhere else in the codebase are they named:</p>
 *
 * <ol>
 *   <li>Acute intoxication and/or withdrawal potential</li>
 *   <li>Biomedical conditions and complications</li>
 *   <li>Emotional, behavioral, or cognitive conditions and complications</li>
 *   <li>Readiness to change</li>
 *   <li>Relapse, continued use, or continued problem potential</li>
 *   <li>Recovery/living environment</li>
 * </ol>
 *
 * <p>Dimension 4 is the counter-intuitive one: a <em>low</em> readiness score reduces the case
 * for residential placement rather than strengthening it. See branch 6 of the ladder.</p>
 */
public class Assessment {

    private long   assessmentId;
    private long   authId;
    private String instrument;      // ASAM_DIM | PHQ9 | GAD7 | CSSRS
    private Integer dimension;      // 1..6 for ASAM_DIM, null otherwise
    private int    score;
    private Date   assessedTs;

    public long getAssessmentId() { return assessmentId; }
    public void setAssessmentId(long assessmentId) { this.assessmentId = assessmentId; }

    public long getAuthId() { return authId; }
    public void setAuthId(long authId) { this.authId = authId; }

    public String getInstrument() { return instrument; }
    public void setInstrument(String instrument) { this.instrument = instrument; }

    public Integer getDimension() { return dimension; }
    public void setDimension(Integer dimension) { this.dimension = dimension; }

    public int getScore() { return score; }
    public void setScore(int score) { this.score = score; }

    public Date getAssessedTs() { return assessedTs; }
    public void setAssessedTs(Date assessedTs) { this.assessedTs = assessedTs; }
}
