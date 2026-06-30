from charts import short_name

DANGER = "#b91c1c"
WARNING = "#b45309"
SUCCESS = "#1a7a5c"
INFO = "#1e40af"


def get_rightsizing_recommendations(client) -> list[dict]:
    try:
        resp = client.get_rightsizing_recommendation(
            Service="AmazonEC2",
            Configuration={"RecommendationTarget": "SAME_INSTANCE_FAMILY", "BenefitsConsidered": True},
        )
        results = []
        for rec in resp.get("RightsizingRecommendations", []):
            current = rec.get("CurrentInstance", {})
            rtype = rec.get("RightsizingType", "")
            if rtype == "TERMINATE":
                results.append({
                    "type": "Terminate",
                    "instance_id": current.get("ResourceId", ""),
                    "instance_type": current.get("InstanceType", ""),
                    "monthly_cost": round(float(current.get("MonthlyCost", 0)), 2),
                    "monthly_savings": round(float(rec.get("TerminateRecommendationDetail", {}).get("EstimatedMonthlySavings", 0)), 2),
                    "region": current.get("AvailabilityZone", ""),
                    "reason": "Idle/underutilized",
                })
            elif rtype == "MODIFY":
                modify = rec.get("ModifyRecommendationDetail", {})
                targets = modify.get("TargetInstances", [])
                if targets:
                    t = targets[0]
                    results.append({
                        "type": "Downsize",
                        "instance_id": current.get("ResourceId", ""),
                        "instance_type": current.get("InstanceType", ""),
                        "recommended_type": t.get("RecommendedResourceType", ""),
                        "monthly_cost": round(float(current.get("MonthlyCost", 0)), 2),
                        "monthly_savings": round(float(t.get("EstimatedMonthlySavings", 0)), 2),
                        "region": current.get("AvailabilityZone", ""),
                        "reason": "Over-provisioned",
                    })
        return results
    except Exception:
        return []


def detect_idle_services(services_dict: dict, threshold: float = 1.0) -> list[dict]:
    idle = []
    for svc, cost in services_dict.items():
        if 0 < cost < threshold:
            idle.append({
                "service": short_name(svc),
                "cost": round(cost, 4),
                "suggestion": f"${cost:.4f}/day spend — consider disabling if unused",
            })
    return sorted(idle, key=lambda x: x["cost"])


def compute_savings_opportunity(services2: dict, savings_plans: dict, reservations: dict) -> list[dict]:
    tips = []

    if savings_plans:
        util = savings_plans.get("utilization", 100)
        unused = savings_plans.get("unused_commitment", 0)
        if util < 80:
            tips.append({
                "category": "Savings Plans",
                "issue": f"Utilization only {util}% — ${unused:,.2f}/month wasted",
                "action": "Review Savings Plan coverage and adjust commitment",
                "severity": "high",
                "estimated_savings": round(unused, 2),
            })

    if reservations:
        util = reservations.get("utilization", 100)
        unused_hours = reservations.get("unused_hours", 0)
        net_savings = reservations.get("net_savings", 0)
        if util < 80:
            tips.append({
                "category": "Reserved Instances",
                "issue": f"RI utilization {util}% — {unused_hours:,.0f} unused hours",
                "action": "Sell unused RIs on Marketplace or modify to better match usage",
                "severity": "high",
                "estimated_savings": round(net_savings * (1 - util / 100), 2),
            })

    s3_cost = sum(v for k, v in services2.items() if "Simple Storage" in k or k == "Amazon Simple Storage Service")
    if s3_cost > 100:
        tips.append({
            "category": "S3 Storage",
            "issue": f"High S3 spend: ${s3_cost:,.2f}",
            "action": "Enable S3 Intelligent-Tiering or lifecycle policies to move cold data to cheaper tiers",
            "severity": "medium",
            "estimated_savings": round(s3_cost * 0.3, 2),
        })

    ec2_cost = sum(v for k, v in services2.items() if "Elastic Compute" in k or "Amazon EC2" in k)
    if ec2_cost > 200:
        tips.append({
            "category": "EC2 Compute",
            "issue": f"High EC2 spend: ${ec2_cost:,.2f}",
            "action": "Consider Spot Instances for non-critical workloads (up to 90% savings)",
            "severity": "medium",
            "estimated_savings": round(ec2_cost * 0.2, 2),
        })

    rds_cost = sum(v for k, v in services2.items() if "Relational Database" in k)
    if rds_cost > 100:
        tips.append({
            "category": "RDS",
            "issue": f"RDS spend: ${rds_cost:,.2f}",
            "action": "Enable RDS auto-pause for dev/test, or consider Aurora Serverless",
            "severity": "low",
            "estimated_savings": round(rds_cost * 0.15, 2),
        })

    return tips


def get_static_tips(services2: dict, total2: float) -> list[dict]:
    tips = []
    sorted_svcs = sorted(services2.items(), key=lambda x: x[1], reverse=True)
    top3 = [k for k, _ in sorted_svcs[:3]]

    for svc in top3:
        sn = short_name(svc)
        cost = services2[svc]
        pct = (cost / total2 * 100) if total2 > 0 else 0
        if pct > 40:
            tips.append({
                "icon": "⚠️",
                "text": f"{sn} accounts for {pct:.0f}% of total spend — review for optimization",
                "severity": "high",
            })

    data_transfer = sum(v for k, v in services2.items() if "data transfer" in k.lower() or "DataTransfer" in k)
    if data_transfer > 50:
        tips.append({
            "icon": "🌐",
            "text": f"${data_transfer:,.2f} in data transfer costs — use VPC endpoints or CloudFront to reduce",
            "severity": "medium",
        })

    cloudwatch_cost = sum(v for k, v in services2.items() if "CloudWatch" in k)
    if cloudwatch_cost > 30:
        tips.append({
            "icon": "📊",
            "text": f"${cloudwatch_cost:,.2f} CloudWatch spend — review log retention periods and metric filters",
            "severity": "low",
        })

    return tips
