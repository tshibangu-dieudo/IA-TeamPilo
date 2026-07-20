"""
Django management command to recalculate risk scores for all active projects.
Intended to be run via cron every 6 hours minimum, per .ai/architecture.md.
See docs/05_Business_Rules.md BR-4.3 for recalculation triggers.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.projects.models import Project
from .services import calculate_risk_score_service


class Command(BaseCommand):
    help = 'Recalculate risk scores for all active projects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=str,
            help='Recalculate risk for a specific project only (by UUID)',
        )

    def handle(self, *args, **options):
        project_id = options.get('project_id')

        if project_id:
            # Recalculate for specific project
            try:
                project = Project.objects.get(id=project_id)
                if project.status != 'active':
                    self.stdout.write(
                        self.style.WARNING(
                            f'Project {project.name} is not active (status: {project.status}). Skipping.'
                        )
                    )
                    return

                risk_score = calculate_risk_score_service(project)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Risk score recalculated for project {project.name}: {risk_score.score}% ({risk_score.level})'
                    )
                )
            except Project.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Project with ID {project_id} not found.')
                )
        else:
            # Recalculate for all active projects
            active_projects = Project.objects.filter(status='active')
            count = active_projects.count()

            if count == 0:
                self.stdout.write(self.style.WARNING('No active projects found.'))
                return

            self.stdout.write(f'Recalculating risk scores for {count} active projects...')

            for project in active_projects:
                try:
                    risk_score = calculate_risk_score_service(project)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  - {project.name}: {risk_score.score}% ({risk_score.level})'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  - {project.name}: ERROR - {str(e)}'
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(f'Risk score recalculation complete for {count} projects.')
            )
