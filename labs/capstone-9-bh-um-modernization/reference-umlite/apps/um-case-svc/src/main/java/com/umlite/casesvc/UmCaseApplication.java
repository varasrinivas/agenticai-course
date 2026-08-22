package com.umlite.casesvc;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling // drives the transactional outbox poller (OutboxPublisher)
public class UmCaseApplication {
    public static void main(String[] args) {
        SpringApplication.run(UmCaseApplication.class, args);
    }
}
