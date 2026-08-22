package com.umlite.casesvc.config;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Configuration;

/**
 * Phase 5 (M25): turn on Spring caching only when {@code um.cache.enabled=true}. Spring Boot then
 * auto-configures a Redis-backed CacheManager (spring.cache.type=redis), so {@code @Cacheable} methods
 * (see CaseQueryService) become cache-aside on Redis. With it off, @EnableCaching is absent, @Cacheable
 * is a no-op, and the service runs without Redis.
 */
@Configuration
@EnableCaching
@ConditionalOnProperty(name = "um.cache.enabled", havingValue = "true")
public class CacheConfig {
}
