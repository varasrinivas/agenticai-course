"""Capstone 9 content, assembled in reading order."""

from c9_sections_a import PART_A
from c9_sections_termmap import PART_TERMMAP
from c9_sections_b import PART_B
from c9_sections_c import PART_C
from c9_sections_d import PART_D

# PART_A already ends with the glossary; the term map slots in ahead of the
# donor section, which is where PART_A places its own marker.
SECTIONS = PART_A + PART_TERMMAP + PART_B + PART_C + PART_D
