package com.bridgeway.bhauth.web;

import org.springframework.beans.PropertyEditorRegistrar;
import org.springframework.beans.PropertyEditorRegistry;
import org.springframework.beans.propertyeditors.CustomDateEditor;

import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * Binds form dates.
 *
 * <p>{@code SimpleDateFormat} is lenient by default and this registrar does not turn that off,
 * so {@code 2016-13-45} parses to a date in 2017 rather than failing. The consequence shows up
 * in eligibility spans that end before they start and in consents whose expiry precedes their
 * signature.</p>
 *
 * <p>The {@code true} passed to {@link CustomDateEditor} means "allow empty", which is why a
 * blank date field silently becomes null instead of a validation error.</p>
 */
public class DateEditorRegistrar implements PropertyEditorRegistrar {

    @Override
    public void registerCustomEditors(PropertyEditorRegistry registry) {
        SimpleDateFormat fmt = new SimpleDateFormat("yyyy-MM-dd");
        // fmt.setLenient(false) -- proposed in 2014, never applied. Turning it on rejected
        // several hundred rows the nightly feed had been quietly accepting, and the feed owner
        // asked for it to be reverted until they could fix the source. They never did.
        registry.registerCustomEditor(Date.class, new CustomDateEditor(fmt, true));
    }
}
