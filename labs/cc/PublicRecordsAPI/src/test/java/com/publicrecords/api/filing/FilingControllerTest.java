package com.publicrecords.api.filing;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
class FilingControllerTest {

    @Autowired
    private MockMvc mvc;

    @Test
    void listsFilingsFromSeedData() throws Exception {
        mvc.perform(get("/filings"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(8));
    }

    @Test
    void filtersByState() throws Exception {
        mvc.perform(get("/filings?state=TX"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(2));
    }

    @Test
    void returnsNotFoundForUnknownId() throws Exception {
        mvc.perform(get("/filings/9999"))
                .andExpect(status().isNotFound());
    }
}
