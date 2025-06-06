import pytest
import uuid
from unittest.mock import patch, MagicMock

from app.services import GitHubActionsService


@pytest.fixture
def github_token():
    return "test-token"


@pytest.fixture
def mock_httpx_post():
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        yield mock_post


@pytest.mark.asyncio
async def test_github_provider_dispatch(github_token, mock_httpx_post):
    provider = GitHubActionsService()
    provider.token = github_token

    job_id = str(uuid.uuid4())
    pipeline_id = str(uuid.uuid4())
    job_data = {
        "app_id": "org.flathub.Test",
        "job_type": "build",
        "params": {
            "owner": "flathub",
            "repo": "actions",
            "workflow_id": "build.yml",
            "ref": "main",
            "inputs": {"flatpak_id": "org.flathub.Test"},
        },
    }

    result = await provider.dispatch(job_id, pipeline_id, job_data)

    mock_httpx_post.assert_called_once()
    args, kwargs = mock_httpx_post.call_args
    assert args[0] == "/repos/flathub/actions/actions/workflows/build.yml/dispatches"

    assert result["status"] == "dispatched"
    assert result["job_id"] == job_id
    assert result["pipeline_id"] == pipeline_id
    assert result["owner"] == "flathub"
    assert result["repo"] == "actions"
    assert result["workflow_id"] == "build.yml"
    assert result["ref"] == "main"


@pytest.mark.asyncio
async def test_github_provider_cancel(github_token, mock_httpx_post):
    provider = GitHubActionsService()
    provider.token = github_token

    job_id = str(uuid.uuid4())
    provider_data = {"owner": "flathub", "repo": "actions", "run_id": 12345}

    mock_httpx_post.return_value.status_code = 202

    result = await provider.cancel(job_id, provider_data)

    mock_httpx_post.assert_called_once()
    args, kwargs = mock_httpx_post.call_args
    assert args[0] == "/repos/flathub/actions/actions/runs/12345/cancel"

    assert result is True


@pytest.mark.asyncio
async def test_github_provider_cancel_missing_run_id(github_token, mock_httpx_post):
    provider = GitHubActionsService()
    provider.token = github_token

    job_id = str(uuid.uuid4())
    provider_data = {"owner": "flathub", "repo": "actions"}

    result = await provider.cancel(job_id, provider_data)

    mock_httpx_post.assert_not_called()
    assert result is False
