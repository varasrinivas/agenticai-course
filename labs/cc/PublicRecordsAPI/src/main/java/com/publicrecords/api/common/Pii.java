package com.publicrecords.api.common;

public final class Pii {

    private Pii() {}

    public static String mask(String value) {
        if (value == null || value.length() < 4) {
            return "***";
        }
        return "***" + value.substring(value.length() - 4);
    }
}
