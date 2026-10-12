# The axial blind spot of a radial cell model: the temperature field a multi-unit model assumes, tested on the LG M50 and a 4680

## The question

Yang, Cui and Tartakovsky (J. Electrochem. Soc. 173 (2026) 050520, doi:10.1149/1945-7111/ae4b6d) resolve the 45 spiral units of an LG M50 cell at their own temperatures and find that a single-unit model at the averaged temperature overestimates the discharge energy, by 3.45 % at 3C and 25 C and by 11.32 % at 2C and minus 5 C, with more than 30 C between units in a 4680 cell. Each unit's temperature comes from a one-dimensional radial conduction model: zero flux at the core, convection with h = 400 W/(m^2 K) at the outer surface, no axial conduction, no end cooling and no tabs.

In the M50 the jelly roll conducts about twenty times better along its layers than across them, so the path to the ends of the cell can matter as much as the path to its side. This study asks what the one-dimensional model leaves out under the paper's own conditions. The heat is held equal, and the paper's radial model is compared with a three-dimensional cell that has an anisotropic roll and a can. The study does not rerun the paper's electrochemistry. It measures the temperature field that the paper's model assumes.

## Status

In progress. The predictions are in `predictions.md`. They are committed and pushed before any three-dimensional field is computed, and every analysis choice is in `DECISIONS.md`.
