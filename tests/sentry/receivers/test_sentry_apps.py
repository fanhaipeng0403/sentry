from __future__ import absolute_import

from mock import patch

from sentry.testutils import APITestCase, TestCase
from sentry.testutils.helpers.faux import faux


@patch('sentry.tasks.sentry_apps.process_resource_change.delay')
class TestIssueSaved(TestCase):
    def test_processes_created_issues(self, delay):
        issue = self.create_group()
        assert faux(delay).called_with(
            action='created',
            sender='Group',
            instance_id=issue.id,
        )

    def test_does_not_process_unless_created(self, delay):
        issue = self.create_group()
        delay.reset_mock()
        issue.update(message='Stuff blew up')
        assert len(delay.mock_calls) == 0


# This testcase needs to be an APITestCase because all of the logic to resolve
# Issues and kick off side effects are just chillin in the endpoint code -_-
@patch('sentry.tasks.sentry_apps.workflow_notification.delay')
class TestIssueResolved(APITestCase):
    def setUp(self):
        self.issue = self.create_group(project=self.project)

        self.sentry_app = self.create_sentry_app(events=['issue.resolved'])

        self.install = self.create_sentry_app_installation(
            organization=self.organization,
            slug=self.sentry_app.slug,
        )

        self.url = u'/api/0/projects/{}/{}/issues/?id={}'.format(
            self.organization.slug,
            self.issue.project.slug,
            self.issue.id,
        )

        self.login_as(self.user)

    def resolve_issue(self, _data=None):
        data = {'status': 'resolved'}
        data.update(_data or {})
        self.client.put(self.url, data=data, format='json')

    def test_notify_after_basic_resolved(self, delay):
        self.resolve_issue()

        assert faux(delay).called_with(
            installation_id=self.install.id,
            issue_id=self.issue.id,
            type='resolved',
            user_id=self.user.id,
        )

    def test_notify_after_resolve_in_commit(self, delay):
        repo = self.create_repo(project=self.project)
        commit = self.create_commit(repo=repo)

        self.resolve_issue({
            'statusDetails': {
                'inCommit': {
                    'repository': repo.name,
                    'commit': commit.key,
                }
            }
        })

        assert faux(delay).called_with(
            installation_id=self.install.id,
            issue_id=self.issue.id,
            type='resolved',
            user_id=self.user.id,
        )

    def test_notify_after_resolve_in_specific_release(self, delay):
        release = self.create_release(project=self.project)

        self.resolve_issue({
            'statusDetails': {
                'inRelease': release.version,
            },
        })

        assert faux(delay).called_with(
            installation_id=self.install.id,
            issue_id=self.issue.id,
            type='resolved',
            user_id=self.user.id,
        )

    def test_notify_after_resolve_in_latest_release(self, delay):
        self.create_release(project=self.project)

        self.resolve_issue({
            'statusDetails': {
                'inRelease': 'latest',
            },
        })

        assert faux(delay).called_with(
            installation_id=self.install.id,
            issue_id=self.issue.id,
            type='resolved',
            user_id=self.user.id,
        )

    def test_notify_after_resolve_in_next_release(self, delay):
        self.create_release(project=self.project)

        self.resolve_issue({
            'statusDetails': {
                'inNextRelease': True,
            },
        })

        assert faux(delay).called_with(
            installation_id=self.install.id,
            issue_id=self.issue.id,
            type='resolved',
            user_id=self.user.id,
        )
