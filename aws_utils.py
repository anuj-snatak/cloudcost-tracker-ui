import boto3
from datetime import datetime, timedelta, date
import calendar


def get_ce_client(access_key, secret_key, region="us-east-1"):
    return boto3.client(
        "ce",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )


def get_ses_client(access_key, secret_key, region="ap-south-1"):
    return boto3.client(
        "ses",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )


def get_sts_client(access_key, secret_key, region="us-east-1"):
    return boto3.client(
        "sts",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )


def assume_role(access_key, secret_key, role_arn, region="us-east-1"):
    sts = get_sts_client(access_key, secret_key, region)
    response = sts.assume_role(RoleArn=role_arn, RoleSessionName="costTrackerUI")
    creds = response["Credentials"]
    return boto3.client(
        "ce",
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
        region_name=region,
    )


def fetch_daily_cost(client, date_str):
    start = datetime.strptime(date_str, "%Y-%m-%d")
    end = start + timedelta(days=1)
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start.strftime("%Y-%m-%d"), "End": end.strftime("%Y-%m-%d")},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    services = {}
    total = 0.0
    for group in response["ResultsByTime"][0].get("Groups", []):
        svc = group["Keys"][0]
        amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
        services[svc] = amt
        total += amt
    return total, services


def fetch_period_cost(client, start_date, end_date):
    days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days
    granularity = "MONTHLY" if days > 31 else "DAILY"
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity=granularity,
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    services = {}
    total = 0.0
    for result in response["ResultsByTime"]:
        for group in result.get("Groups", []):
            svc = group["Keys"][0]
            amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
            services[svc] = services.get(svc, 0.0) + amt
            total += amt
    return total, services


def fetch_daily_trend(client, days=14):
    end = date.today()
    start = end - timedelta(days=days)
    response = client.get_cost_and_usage(
        TimePeriod={"Start": str(start), "End": str(end)},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
    )
    trend = []
    for result in response["ResultsByTime"]:
        d = result["TimePeriod"]["Start"]
        amt = float(result["Total"]["UnblendedCost"]["Amount"])
        trend.append({"date": d, "cost": round(amt, 2)})
    return trend


def fetch_service_daily_trend(client, days=14):
    end = date.today()
    start = end - timedelta(days=days)
    response = client.get_cost_and_usage(
        TimePeriod={"Start": str(start), "End": str(end)},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    data = []
    for result in response["ResultsByTime"]:
        d = result["TimePeriod"]["Start"]
        for group in result.get("Groups", []):
            svc = group["Keys"][0]
            amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if amt > 0.01:
                data.append({"date": d, "service": svc, "cost": round(amt, 2)})
    return data


def get_forecast(client):
    today = date.today()
    next_month = date(today.year + (today.month == 12), (today.month % 12) + 1, 1)
    response = client.get_cost_forecast(
        TimePeriod={"Start": today.strftime("%Y-%m-%d"), "End": next_month.strftime("%Y-%m-%d")},
        Metric="UNBLENDED_COST",
        Granularity="MONTHLY",
    )
    return round(float(response["Total"]["Amount"]), 2)


def get_last_month_total(client):
    today = datetime.now()
    first_this = datetime(today.year, today.month, 1)
    last_prev = first_this - timedelta(days=1)
    first_prev = datetime(last_prev.year, last_prev.month, 1)
    response = client.get_cost_and_usage(
        TimePeriod={"Start": first_prev.strftime("%Y-%m-%d"), "End": first_this.strftime("%Y-%m-%d")},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )
    return round(float(response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]), 2)


def get_current_month_spend(client):
    today = date.today()
    first = today.replace(day=1)
    response = client.get_cost_and_usage(
        TimePeriod={"Start": str(first), "End": str(today)},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )
    return round(float(response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]), 2)


def get_anomalies(client, date1, date2):
    try:
        response = client.get_anomalies(
            DateInterval={"StartDate": date1, "EndDate": date2}
        )
        anomalies = response.get("Anomalies", [])
        results = []
        for anom in anomalies:
            impact = float(anom.get("Impact", {}).get("TotalImpact", 0))
            root_causes = []
            for rc in anom.get("RootCauses", []):
                root_causes.append({
                    "Service": rc.get("Service", "Unknown"),
                    "Region": rc.get("Region", "N/A"),
                    "Usage Type": rc.get("UsageType", "N/A"),
                    "Linked Account": rc.get("LinkedAccountName", "N/A"),
                })
            results.append({
                "start_date": anom.get("AnomalyStartDate", ""),
                "end_date": anom.get("AnomalyEndDate", ""),
                "impact": impact,
                "root_causes": root_causes,
            })
        results.sort(key=lambda x: abs(x["impact"]), reverse=True)
        return results
    except Exception:
        return []


def fetch_cost_by_region(client, start_date, end_date):
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity="MONTHLY" if (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days > 31 else "DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "REGION"}],
    )
    regions = {}
    for result in response["ResultsByTime"]:
        for group in result.get("Groups", []):
            rgn = group["Keys"][0]
            amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if amt > 0.01:
                regions[rgn] = regions.get(rgn, 0.0) + round(amt, 2)
    return regions


def fetch_cost_by_account(client, start_date, end_date):
    try:
        response = client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="MONTHLY" if (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days > 31 else "DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
        )
        accounts = {}
        for result in response["ResultsByTime"]:
            for group in result.get("Groups", []):
                acc = group["Keys"][0]
                amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
                if amt > 0.01:
                    accounts[acc] = accounts.get(acc, 0.0) + round(amt, 2)
        return accounts
    except Exception:
        return {}


def fetch_cost_by_usage_type(client, start_date, end_date):
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity="MONTHLY" if (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days > 31 else "DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "USAGE_TYPE"}],
    )
    usage = {}
    for result in response["ResultsByTime"]:
        for group in result.get("Groups", []):
            ut = group["Keys"][0]
            amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if amt > 0.5:
                usage[ut] = usage.get(ut, 0.0) + round(amt, 2)
    return dict(sorted(usage.items(), key=lambda x: x[1], reverse=True)[:20])


def fetch_custom_range_cost(client, start_date, end_date):
    days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity="MONTHLY" if days > 31 else "DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    services = {}
    total = 0.0
    for result in response["ResultsByTime"]:
        for group in result.get("Groups", []):
            svc = group["Keys"][0]
            amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
            services[svc] = services.get(svc, 0.0) + amt
            total += amt
    return round(total, 2), services


def get_savings_plans_utilization(client):
    try:
        today = date.today()
        first = today.replace(day=1)
        response = client.get_savings_plans_utilization(
            TimePeriod={"Start": str(first), "End": str(today)},
            Granularity="MONTHLY",
        )
        total = response["Total"]
        return {
            "utilization": round(float(total["Utilization"]["UtilizationPercentage"]), 1),
            "savings": round(float(total["Savings"]["NetSavings"]), 2),
            "total_commitment": round(float(total["Utilization"]["TotalCommitment"]), 2),
            "used_commitment": round(float(total["Utilization"]["UsedCommitment"]), 2),
            "unused_commitment": round(float(total["Utilization"]["UnusedCommitment"]), 2),
        }
    except Exception:
        return None


def get_reservation_utilization(client):
    try:
        today = date.today()
        first = today.replace(day=1)
        response = client.get_reservation_utilization(
            TimePeriod={"Start": str(first), "End": str(today)},
            Granularity="MONTHLY",
        )
        total = response["Total"]
        return {
            "utilization": round(float(total["UtilizationPercentage"]), 1),
            "purchased_hours": round(float(total["PurchasedHours"]), 1),
            "used_hours": round(float(total["TotalActualHours"]), 1),
            "unused_hours": round(float(total["UnusedHours"]), 1),
            "net_savings": round(float(total["NetRISavings"]), 2),
        }
    except Exception:
        return None


def fetch_service_detail(client, service_name, days=14, start_date=None, end_date=None):
    """Deep dive into a single service — daily trend, region, usage type."""
    if start_date and end_date:
        start = start_date if isinstance(start_date, date) else datetime.strptime(str(start_date), "%Y-%m-%d").date()
        end = end_date if isinstance(end_date, date) else datetime.strptime(str(end_date), "%Y-%m-%d").date()
    else:
        end = date.today()
        start = end - timedelta(days=days)

    actual_days = (end - start).days
    granularity = "MONTHLY" if actual_days > 31 else "DAILY"

    trend_resp = client.get_cost_and_usage(
        TimePeriod={"Start": str(start), "End": str(end)},
        Granularity=granularity,
        Metrics=["UnblendedCost"],
        Filter={"Dimensions": {"Key": "SERVICE", "Values": [service_name]}},
    )
    trend = []
    for result in trend_resp["ResultsByTime"]:
        d = result["TimePeriod"]["Start"]
        amt = float(result["Total"]["UnblendedCost"]["Amount"])
        trend.append({"date": d, "cost": round(amt, 2)})

    region_resp = client.get_cost_and_usage(
        TimePeriod={"Start": str(start), "End": str(end)},
        Granularity=granularity,
        Metrics=["UnblendedCost"],
        Filter={"Dimensions": {"Key": "SERVICE", "Values": [service_name]}},
        GroupBy=[{"Type": "DIMENSION", "Key": "REGION"}],
    )
    regions = {}
    for result in region_resp["ResultsByTime"]:
        for group in result.get("Groups", []):
            rgn = group["Keys"][0]
            amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if amt > 0.01:
                regions[rgn] = regions.get(rgn, 0.0) + round(amt, 2)

    usage_resp = client.get_cost_and_usage(
        TimePeriod={"Start": str(start), "End": str(end)},
        Granularity=granularity,
        Metrics=["UnblendedCost"],
        Filter={"Dimensions": {"Key": "SERVICE", "Values": [service_name]}},
        GroupBy=[{"Type": "DIMENSION", "Key": "USAGE_TYPE"}],
    )
    usage = {}
    for result in usage_resp["ResultsByTime"]:
        for group in result.get("Groups", []):
            ut = group["Keys"][0]
            amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if amt > 0.01:
                usage[ut] = usage.get(ut, 0.0) + round(amt, 2)

    return {
        "trend": trend,
        "regions": dict(sorted(regions.items(), key=lambda x: x[1], reverse=True)),
        "usage_types": dict(sorted(usage.items(), key=lambda x: x[1], reverse=True)[:15]),
        "total": round(sum(d["cost"] for d in trend), 2),
        "start": str(start),
        "end": str(end),
    }


def fetch_multi_service_trend(client, service_names, days=14, start_date=None, end_date=None):
    """Daily trend for multiple services side-by-side."""
    if start_date and end_date:
        start = start_date if isinstance(start_date, date) else datetime.strptime(str(start_date), "%Y-%m-%d").date()
        end = end_date if isinstance(end_date, date) else datetime.strptime(str(end_date), "%Y-%m-%d").date()
    else:
        end = date.today()
        start = end - timedelta(days=days)
    response = client.get_cost_and_usage(
        TimePeriod={"Start": str(start), "End": str(end)},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        Filter={"Dimensions": {"Key": "SERVICE", "Values": service_names}},
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    data = []
    for result in response["ResultsByTime"]:
        d = result["TimePeriod"]["Start"]
        for group in result.get("Groups", []):
            svc = group["Keys"][0]
            amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
            data.append({"date": d, "service": svc, "cost": round(amt, 2)})
    return data


def fetch_available_tag_keys(client) -> list[str]:
    try:
        end = date.today()
        start = end - timedelta(days=90)
        resp = client.get_tags(
            TimePeriod={"Start": str(start), "End": str(end)},
        )
        return sorted(resp.get("Tags", []))
    except Exception:
        return []


def fetch_cost_by_tag(client, tag_key: str, start_date: str, end_date: str) -> dict:
    try:
        days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days
        granularity = "MONTHLY" if days > 31 else "DAILY"
        resp = client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity=granularity,
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "TAG", "Key": tag_key}],
        )
        tags = {}
        for result in resp["ResultsByTime"]:
            for group in result.get("Groups", []):
                tag_val = group["Keys"][0].replace(f"{tag_key}$", "")
                amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
                if amt > 0.01:
                    tags[tag_val or "(untagged)"] = tags.get(tag_val or "(untagged)", 0.0) + round(amt, 2)
        return dict(sorted(tags.items(), key=lambda x: x[1], reverse=True))
    except Exception:
        return {}


def fetch_cost_by_tag_and_service(client, tag_key: str, tag_value: str, start_date: str, end_date: str) -> dict:
    try:
        days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days
        granularity = "MONTHLY" if days > 31 else "DAILY"
        resp = client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity=granularity,
            Metrics=["UnblendedCost"],
            Filter={"Tags": {"Key": tag_key, "Values": [tag_value]}},
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
        services = {}
        for result in resp["ResultsByTime"]:
            for group in result.get("Groups", []):
                svc = group["Keys"][0]
                amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
                if amt > 0.01:
                    services[svc] = services.get(svc, 0.0) + round(amt, 2)
        return dict(sorted(services.items(), key=lambda x: x[1], reverse=True))
    except Exception:
        return {}


def fetch_s3_bucket_cost(client, start_date: str, end_date: str) -> dict:
    try:
        days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days
        granularity = "MONTHLY" if days > 31 else "DAILY"
        resp = client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity=granularity,
            Metrics=["UnblendedCost"],
            Filter={"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Simple Storage Service"]}},
            GroupBy=[{"Type": "DIMENSION", "Key": "USAGE_TYPE"}],
        )
        usage = {}
        for result in resp["ResultsByTime"]:
            for group in result.get("Groups", []):
                ut = group["Keys"][0]
                amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
                if amt > 0.001:
                    usage[ut] = usage.get(ut, 0.0) + round(amt, 4)
        return dict(sorted(usage.items(), key=lambda x: x[1], reverse=True))
    except Exception:
        return {}


def fetch_ec2_instance_type_cost(client, start_date: str, end_date: str) -> dict:
    try:
        days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days
        granularity = "MONTHLY" if days > 31 else "DAILY"
        resp = client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity=granularity,
            Metrics=["UnblendedCost"],
            Filter={"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Elastic Compute Cloud - Compute"]}},
            GroupBy=[{"Type": "DIMENSION", "Key": "INSTANCE_TYPE"}],
        )
        instances = {}
        for result in resp["ResultsByTime"]:
            for group in result.get("Groups", []):
                itype = group["Keys"][0]
                amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
                if amt > 0.01 and itype != "NoInstanceType":
                    instances[itype] = instances.get(itype, 0.0) + round(amt, 2)
        return dict(sorted(instances.items(), key=lambda x: x[1], reverse=True))
    except Exception:
        return {}


def get_date_ranges(mode, ref_date):
    """Returns (date1, date2, period_start, period_end) — all End dates are API-exclusive (day after last day)."""
    if mode == "Daily":
        d1 = ref_date - timedelta(days=1)
        d2 = ref_date
        return str(d1), str(d2), str(d1), str(d2)
    elif mode == "Weekly":
        curr_start = ref_date - timedelta(days=ref_date.weekday())
        curr_end = curr_start + timedelta(days=7)
        prev_start = curr_start - timedelta(days=7)
        return str(prev_start), str(curr_start), str(curr_start), str(curr_end)
    else:
        curr_start = ref_date.replace(day=1)
        _, last_day = calendar.monthrange(ref_date.year, ref_date.month)
        curr_end = ref_date.replace(day=last_day) + timedelta(days=1)
        prev_end = curr_start
        prev_start = (prev_end - timedelta(days=1)).replace(day=1)
        return str(prev_start), str(prev_end), str(curr_start), str(curr_end)
