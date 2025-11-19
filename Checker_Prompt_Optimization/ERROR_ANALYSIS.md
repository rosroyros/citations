# Detailed Error Analysis: GPT-5-mini_optimized

## Summary

- Total errors: 21
- False positives (too strict): 16
- False negatives (too lenient): 5

## False Positives by Issue Type

- no_specific_issue_listed: [{'citation': 'joachimr., & smithj. (2019, November 19). We are relying on APA as our university style format - the university is located in Germany (Kassel). So I [Comment on the blog post “The transition to seventh edition APA Style”]. _APA Style_. https://apastyle.apa.org/blog/transition-seventh-edition#comment-4694866690', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'Evans, A. C., Jr., Garbarino, J., Bocanegra, E., Kinscherff, R. T., & Márquez-Greene, N. (2019, August 8–11). _Gun violence: An event on the power of community_ [Conference presentation]. APA 2019 Convention, Chicago, IL, USA. doi:10.1037/con2019-1234', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'Cacioppo, S. (2019, April 25–28). _Evolutionary theory of social connections: Past, present, and future_ [Conference presentation abstract]. Ninety-ninth annual convention of the Western Psychological Association, Pasadena, California, United States. https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final-2.pdf', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'Duckworth, A. L., Quirk, A., Gallop, R., Hoyle, R. H., Kelly, D. R., & Matthews, M. D. (2019). Cognitive and noncognitive predictors of success. _Proceedings of the National Academy of Sciences_, _USA_, _116_(47), 23499–23504. https://doi.org/10.1073/pnas.1910510116', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'Kushilevitz, E., & Malkin, T. (Eds.). (2016). _Lecture notes in computer science: Vol. 9562. Theory of cryptography_. Springer. https://doi.org/10.1007/978-3-662-49096-9', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'Plato (1989). _Symposium_ (A. Nehamas & P. Woodruff, Trans.). Hackett Publishing Company.', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'American Psychiatric Association. (2000). _Diagnostic and statistical manual of mental disorders_ (4th ed., text rev.). https://doi.org/10.1176/appi.books.9780890420249.dsm-iv-tr', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'Thestrup, K. (2010). To transform, to communicate, to play—The experimenting community in action. In E. Hygum & P. M. Pedersen (Eds.), _Early childhood education: Values and practices in Denmark_. Hans Reitzels Forlag. https://earlychildhoodeducation.digi.hansreitzel.dk/?id=192', 'source': 'manual_curation', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'Jerrentrup, A., Mueller, T., Glowalla, U., & Schaefer, J. R. (2018). Teaching medicine with the help of “Dr. House.” _PLoS ONE_, _13_(3), Article e0193972. https://doi.org/10.1371/journal.pone.0193972', 'source': 'synthetic_expansion', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'Plato (1989). _Symposium_ (A. Nehamas & P. Woodruff, Trans.). Hackett Publishing Co. (Original work published 385-378 BCE)', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'Armstrong, D. (2019). Malory and Character. In M. G. Leitch & C. J. Rushton (Eds.), _A new companion to Malory_ (pp. 144-163). D. S. Brewer. https://doi.org/10.1234/abcd.5678', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'Jerrentrup, A., Mueller, T., Glowalla, U., Herder, M., & Henrichs, N. (2018). Teaching medicine with the help of Dr. House. PLoS ONE, 13(3), Article e0193972. https://doi.org/10.1371/journal.pone.0193972', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'National Cancer Institute. (2019). _Taking time_: Support for people with cancer (NIH Publication No. 18-2059). U.S. Department of Health and Human Services, National Institutes of Health. https://www.cancer.gov/publications/patient-education/takingtime.pdf', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'Perreault, L. (2019). Obesity in adults: Role of physical activity and exercise. _UpToDate_. Retrieved January 12, 2020, from https://www.uptodate.com/contents/obesity-in-adults-role-of-physical-activity-and-exercise', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'Agency for Toxic Substances and Disease Registry. (n.d.). _Asbestos in your environment: What you can do to limit exposure_ [Fact sheet]. U.S. Department of Health & Human Services. https://www.atsdr.cdc.gov/docs/limitingenvironmentalexposures_factsheet-508.pdf', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}, {'citation': 'Ouellette, J. (2019, November 15). Physicists capture first footage of quantum knots unraveling in superfluid. _Ars Technica_. https://doi.org/10.1234/5678', 'source': 'unknown', 'predicted': False, 'ground_truth': True, 'explanation': '', 'issues_flagged': []}] cases

## Errors by Source Type

### unknown
- Total errors: 19
- False positives: 14
- False negatives: 5

### manual_curation
- Total errors: 1
- False positives: 1
- False negatives: 0

### synthetic_expansion
- Total errors: 1
- False positives: 1
- False negatives: 0

## Recommended Prompt Improvements

1. **no_specific_issue_listed** (16 errors)
   - Type: false_positive
   - Change: TO BE DETERMINED BY MANUAL ANALYSIS

