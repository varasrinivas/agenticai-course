package com.umlite.casesvc.events;

/** Kafka topic names — the Java mirror of libs/events (@um-lite/events). Past-tense facts. */
public final class Topics {
    private Topics() { }

    public static final String PA_SUBMITTED = "pa.submitted";
    public static final String PA_DECISIONED = "pa.decisioned";
    public static final String PA_DEAD_LETTER = "pa.dead-letter";
}
