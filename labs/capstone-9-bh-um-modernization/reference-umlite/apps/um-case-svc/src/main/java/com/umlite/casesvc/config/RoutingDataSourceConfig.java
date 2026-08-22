package com.umlite.casesvc.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.jdbc.DataSourceBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.jdbc.datasource.lookup.AbstractRoutingDataSource;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import javax.sql.DataSource;
import java.util.HashMap;
import java.util.Map;

/**
 * Read/write datasource routing (Phase 5 / Track 5, M27). Active only when {@code um.replica.enabled=true}.
 * Read-only transactions ({@code @Transactional(readOnly = true)}) are routed to the Postgres read
 * replica; everything else (writes, Flyway, default) goes to the primary. When disabled, Spring Boot's
 * normal single-DataSource auto-config applies, so the service runs against one node as before.
 */
@Configuration
@ConditionalOnProperty(name = "um.replica.enabled", havingValue = "true")
public class RoutingDataSourceConfig {

    private static final String PRIMARY = "primary";
    private static final String REPLICA = "replica";

    @Bean
    @Primary
    public DataSource dataSource(
            @Value("${spring.datasource.url}") String primaryUrl,
            @Value("${um.replica.url}") String replicaUrl,
            @Value("${spring.datasource.username}") String username,
            @Value("${spring.datasource.password}") String password) {

        DataSource primary = DataSourceBuilder.create()
                .url(primaryUrl).username(username).password(password).build();
        DataSource replica = DataSourceBuilder.create()
                .url(replicaUrl).username(username).password(password).build();

        Map<Object, Object> targets = new HashMap<>();
        targets.put(PRIMARY, primary);
        targets.put(REPLICA, replica);

        AbstractRoutingDataSource routing = new AbstractRoutingDataSource() {
            @Override
            protected Object determineCurrentLookupKey() {
                // Reads in a read-only transaction → replica; writes → primary.
                return TransactionSynchronizationManager.isCurrentTransactionReadOnly() ? REPLICA : PRIMARY;
            }
        };
        routing.setTargetDataSources(targets);
        routing.setDefaultTargetDataSource(primary);
        return routing;
    }
}
