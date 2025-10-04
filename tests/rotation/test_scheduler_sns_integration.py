import os
import subprocess
import time
from datetime import UTC, datetime, timedelta

import boto3
import pytest
import requests
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=False)

# Make sure no stray LocalStack/custom endpoint is used
for v in ("AWS_ENDPOINT_URL", "AWS_ENDPOINT"):
    os.environ.pop(v, None)

VAULTWARDEN_URL = os.getenv("VAULTWARDEN_URL", "http://localhost:3000").rstrip("/")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

AWS_REGION = os.getenv("AWS_SNS_REGION", "eu-west-1")
TOPIC_ARN = os.getenv("ROTATION_SNS_TOPIC_ARN")
TOPIC_NAME = os.getenv("ROTATION_TOPIC_NAME")  # optional fallback
SCHED_IMAGE = os.getenv("ROTATION_IMAGE", "hadiserhan/vw-rotation:latest")

# force candidates so a publish happens
FREQ_DAYS = os.getenv("ROTATION_FREQUENCY_DAYS", "0")
GRACE_DAYS = os.getenv("ROTATION_GRACE_PERIOD_DAYS", "0")


def _sns():
    return boto3.client("sns", region_name=AWS_REGION)


def _cw():
    return boto3.client("cloudwatch", region_name=AWS_REGION)


def _resolve_topic_arn() -> str:
    if TOPIC_ARN:
        return TOPIC_ARN
    if not TOPIC_NAME:
        pytest.fail("Set ROTATION_SNS_TOPIC_ARN or ROTATION_TOPIC_NAME in .env")
    token = None
    while True:
        resp = _sns().list_topics(NextToken=token) if token else _sns().list_topics()
        for t in resp.get("Topics", []):
            arn = t.get("TopicArn", "")
            if arn.split(":")[-1] == TOPIC_NAME:
                return arn
        token = resp.get("NextToken")
        if not token:
            break
    return _sns().create_topic(Name=TOPIC_NAME)["TopicArn"]


def _topic_name_from_arn(arn: str) -> str:
    return arn.split(":")[-1]


def _get_publish_count(topic_name: str, start: datetime, end: datetime) -> float:
    resp = _cw().get_metric_statistics(
        Namespace="AWS/SNS",
        MetricName="NumberOfMessagesPublished",
        Dimensions=[{"Name": "TopicName", "Value": topic_name}],
        StartTime=start,
        EndTime=end,
        Period=60,
        Statistics=["Sum"],
        Unit="Count",
    )
    return sum(dp.get("Sum", 0.0) for dp in resp.get("Datapoints", []))


def _run_scheduler_once(topic_arn: str):
    env = {
        "VAULTWARDEN_URL": VAULTWARDEN_URL,
        "CLIENT_ID": CLIENT_ID,
        "CLIENT_SECRET": CLIENT_SECRET,
        "AWS_SNS_REGION": AWS_REGION,
        "ROTATION_SNS_TOPIC_ARN": topic_arn,
        "ROTATION_RUN_ONCE": "1",
        "ROTATION_DRY_RUN": "0",
        "ROTATION_FREQUENCY_DAYS": FREQ_DAYS,
        "ROTATION_GRACE_PERIOD_DAYS": GRACE_DAYS,
        "ROTATION_SNS_DIGEST": "0",
        "ROTATION_LOG_LEVEL": "DEBUG",
        "AWS_EC2_METADATA_DISABLED": "true",
    }

    # pass AWS creds if set in the host env or .env
    for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        v = os.getenv(k)
        if v:
            env[k] = v

    args = ["docker", "run", "--rm"]
    for k, v in env.items():
        args += ["-e", f"{k}={v}"]

    if os.getenv("USE_DOCKER_HOST_NETWORK", "1").lower() in ("1", "true", "yes"):
        args.append("--network=host")

    args.append(SCHED_IMAGE)

    proc = subprocess.run(args, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise AssertionError(
            f"exit {proc.returncode}\n---stdout---\n{proc.stdout}\n---stderr---\n{proc.stderr}"
        )


def test_sns_metric_increases_after_scheduler_run():
    if not CLIENT_ID or not CLIENT_SECRET:
        pytest.skip("CLIENT_ID/CLIENT_SECRET missing in env")

    try:
        assert requests.get(f"{VAULTWARDEN_URL}/alive", timeout=5).status_code == 200
    except Exception as e:
        pytest.skip(f"Vaultwarden not reachable: {e}")

    topic_arn = _resolve_topic_arn()
    topic_name = _topic_name_from_arn(topic_arn)

    now = datetime.now(UTC)
    baseline = _get_publish_count(topic_name, now - timedelta(minutes=10), now)

    start_run = datetime.now(UTC)
    _run_scheduler_once(topic_arn)

    # CW can lag; poll up to 3 minutes
    deadline = time.time() + 180
    last_val = baseline
    while time.time() < deadline:
        val = _get_publish_count(topic_name, start_run - timedelta(minutes=1), datetime.now(UTC))
        last_val = val
        if val >= baseline + 1:
            break
        time.sleep(10)

    assert last_val >= baseline + 1, (
        f"SNS metric didn't increase. baseline={baseline}, latest={last_val}, topic={topic_name}"
    )
