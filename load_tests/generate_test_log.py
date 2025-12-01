#!/usr/bin/env python3
"""
Generate large test citation log file for parser performance testing
"""

import os
import sys
import time
from pathlib import Path

def create_large_citation_log(num_jobs=4000, citations_per_job=8):
    """Generate large test log file"""
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    log_dir = project_dir / 'logs'

    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, 'citations_test.log')

    print(f'Generating {num_jobs} jobs with {citations_per_job} citations each...')
    print(f'Output file: {log_path}')

    # Sample citation templates for variety
    citation_templates = [
        '{author}. {title}. {publisher}, {year}.',
        '{author}. "{title}" {journal}, {volume}({issue}): {pages}, {year}.',
        '{author}. {title}. PhD thesis, {university}, {year}.',
        '{author}. {title}. In {conference}, pp. {pages}, {year}.',
        '{author} and {coauthor}. {title}. {publisher}, {year}.'
    ]

    authors = [
        'Smith J', 'Johnson A', 'Williams B', 'Brown C', 'Davis D',
        'Miller E', 'Wilson F', 'Moore G', 'Taylor H', 'Anderson K',
        'Thomas L', 'Jackson M', 'White N', 'Harris P', 'Martin S'
    ]

    titles = [
        'A Study on Advanced Methods', 'Machine Learning Applications',
        'Data Analysis Techniques', 'Computational Intelligence',
        'Algorithm Design Patterns', 'Software Engineering Best Practices',
        'Database Optimization Strategies', 'Network Security Fundamentals'
    ]

    publishers = [
        'ACM Press', 'IEEE Computer Society', 'Springer', 'Oxford University Press',
        'Cambridge University Press', 'MIT Press', 'Wiley', 'Elsevier'
    ]

    start_time = time.time()

    with open(log_path, 'w') as f:
        for job_id in range(num_jobs):
            f.write(f'<<JOB_ID:test-load-job-{job_id:04d}>>\n')

            for citation_num in range(citations_per_job):
                # Create varied citations
                template = citation_templates[citation_num % len(citation_templates)]
                author = authors[(job_id + citation_num) % len(authors)]
                title = titles[(job_id + citation_num * 2) % len(titles)]
                publisher = publishers[(job_id + citation_num * 3) % len(publishers)]
                year = 2020 + (job_id % 4)

                if 'journal' in template:
                    journal = f'Journal of {titles[job_id % len(titles)]}'
                    volume = 10 + (job_id % 20)
                    issue = 1 + (job_id % 6)
                    pages = f'{100 + job_id % 900}-{105 + job_id % 900}'

                    citation = template.format(
                        author=author,
                        title=title,
                        journal=journal,
                        volume=volume,
                        issue=issue,
                        pages=pages,
                        year=year
                    )
                elif 'university' in template:
                    universities = ['Stanford University', 'MIT', 'CMU', 'UC Berkeley', 'University of Washington']
                    university = universities[job_id % len(universities)]
                    citation = template.format(author=author, title=title, university=university, year=year)
                elif 'conference' in template:
                    conferences = ['ICML', 'NeurIPS', 'ICLR', 'AAAI', 'IJCAI']
                    conference = conferences[job_id % len(conferences)]
                    pages = f'{100 + job_id % 2000}-{105 + job_id % 2000}'
                    citation = template.format(author=author, title=title, conference=conference, pages=pages, year=year)
                elif 'coauthor' in template:
                    coauthor = authors[(job_id + citation_num + 1) % len(authors)]
                    citation = template.format(author=author, coauthor=coauthor, title=title, publisher=publisher, year=year)
                else:
                    citation = template.format(author=author, title=title, publisher=publisher, year=year)

                # Add some realistic text to simulate production data
                citation += f" This citation represents a realistic academic reference with sufficient detail to simulate production data volume and variety of source types."

                f.write(f'{citation}\n')

            f.write('<<<END_JOB>>>\n')

            # Progress indicator
            if (job_id + 1) % 500 == 0:
                print(f'Generated {job_id + 1}/{num_jobs} jobs...')

    end_time = time.time()
    generation_time = end_time - start_time

    file_size = os.path.getsize(log_path)

    print(f'\n=== GENERATION COMPLETE ===')
    print(f'Generated {num_jobs} jobs with {citations_per_job} citations each')
    print(f'Total citations: {num_jobs * citations_per_job}')
    print(f'Generation time: {generation_time:.2f} seconds')
    print(f'Log file size: {file_size / (1024*1024):.1f} MB')
    print(f'File location: {log_path}')

    return log_path

if __name__ == '__main__':
    # Allow customization from command line
    num_jobs = 4000
    citations_per_job = 8

    if len(sys.argv) > 1:
        num_jobs = int(sys.argv[1])
    if len(sys.argv) > 2:
        citations_per_job = int(sys.argv[2])

    log_path = create_large_citation_log(num_jobs, citations_per_job)
    print(f'\nReady for parser performance testing with: {log_path}')