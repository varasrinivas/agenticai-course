package com.umlite.casesvc.config;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

/**
 * Phase 5 (M28): OIDC resource-server security.
 *
 * When {@code um.security.enabled=true}, the service requires a valid JWT (issued by Keycloak — see
 * spring.security.oauth2.resourceserver.jwt.issuer-uri) on every request except actuator health.
 * When off (default), an open chain permits everything so the REST/event/workflow labs keep working
 * without an identity provider. Adding spring-security to the classpath would otherwise lock the app
 * down by default — these explicit chains make the behavior a deliberate toggle.
 */
@Configuration
public class SecurityConfig {

    /** Secured chain — validate Keycloak JWTs as a resource server. */
    @Bean
    @ConditionalOnProperty(name = "um.security.enabled", havingValue = "true")
    public SecurityFilterChain securedChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/**").permitAll()
                .anyRequest().authenticated())
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(jwt -> { }))
            .csrf(csrf -> csrf.disable());
        return http.build();
    }

    /** Open chain — default, so the service runs without an identity provider. */
    @Bean
    @ConditionalOnProperty(name = "um.security.enabled", havingValue = "false", matchIfMissing = true)
    public SecurityFilterChain openChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth.anyRequest().permitAll())
            .csrf(csrf -> csrf.disable());
        return http.build();
    }
}
