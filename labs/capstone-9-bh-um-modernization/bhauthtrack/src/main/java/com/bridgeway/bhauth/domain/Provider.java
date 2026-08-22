package com.bridgeway.bhauth.domain;

/**
 * A treating provider or facility. Maps onto BH_PROVIDER.
 *
 * <p>{@code part2Program} marks a federally assisted substance-use-disorder treatment program.
 * Records that originate from one carry a redisclosure restriction that ordinary behavioral
 * health records do not — the whole 42 CFR Part 2 regime hangs off this single character
 * column.</p>
 *
 * <p><b>It has been wrong before.</b> The flag was added in 2014 (BHA-3390) and backfilled from
 * a spreadsheet supplied by network management. The accuracy of that backfill has never been
 * audited. {@link com.bridgeway.bhauth.service.AuthCaseService#submitAndDecide} captures consent
 * unconditionally, rather than only when this flag is set, precisely because nobody trusts
 * it.</p>
 *
 * <p>Note what this means for a port: the flag is an <em>input</em> to a regulatory control and
 * it is known-unreliable. Treating it as authoritative — for example, by only applying Part 2
 * handling when it is {@code Y} — makes the system less safe than the one being replaced.</p>
 */
public class Provider {

    private String bridgewayProvId;
    private String npi;
    private String providerName;
    private String networkStatus;      // IN | OUT | TERMED
    private String isPart2Program;     // 'Y' | 'N'

    /** Named {@code isPart2Program()} so JSTL can reach it as {@code ${provider.part2Program}}. */
    public boolean isPart2Program() { return "Y".equals(isPart2Program); }

    public String getBridgewayProvId() { return bridgewayProvId; }
    public void setBridgewayProvId(String id) { this.bridgewayProvId = id; }

    public String getNpi() { return npi; }
    public void setNpi(String npi) { this.npi = npi; }

    public String getProviderName() { return providerName; }
    public void setProviderName(String providerName) { this.providerName = providerName; }

    public String getNetworkStatus() { return networkStatus; }
    public void setNetworkStatus(String networkStatus) { this.networkStatus = networkStatus; }

    public String getIsPart2Program() { return isPart2Program; }
    public void setIsPart2Program(String v) { this.isPart2Program = v; }
}
