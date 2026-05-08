package com.publicrecords.api.filing;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.Instant;

@Entity
@Table(name = "filings")
public class Filing {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank
    @Size(min = 2, max = 2)
    @Column(nullable = false, length = 2)
    private String state;

    @NotBlank
    @Column(name = "debtor_name", nullable = false)
    private String debtorName;

    @NotBlank
    @Column(name = "secured_party", nullable = false)
    private String securedParty;

    @Column(name = "collateral_description", length = 1000)
    private String collateralDescription;

    @Column(name = "filed_at", nullable = false)
    private Instant filedAt;

    @Column(name = "expires_at")
    private Instant expiresAt;

    public Filing() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getState() { return state; }
    public void setState(String state) { this.state = state; }
    public String getDebtorName() { return debtorName; }
    public void setDebtorName(String debtorName) { this.debtorName = debtorName; }
    public String getSecuredParty() { return securedParty; }
    public void setSecuredParty(String securedParty) { this.securedParty = securedParty; }
    public String getCollateralDescription() { return collateralDescription; }
    public void setCollateralDescription(String collateralDescription) { this.collateralDescription = collateralDescription; }
    public Instant getFiledAt() { return filedAt; }
    public void setFiledAt(Instant filedAt) { this.filedAt = filedAt; }
    public Instant getExpiresAt() { return expiresAt; }
    public void setExpiresAt(Instant expiresAt) { this.expiresAt = expiresAt; }
}
