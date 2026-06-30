import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

SERVICE_NAME_MAPPING = {
    "ACM": "AWS Certificate Manager", "APIGateway": "Amazon API Gateway",
    "CloudFront": "Amazon CloudFront", "CloudWatch": "Amazon CloudWatch",
    "DynamoDB": "Amazon DynamoDB", "EBS": "Amazon Elastic Block Store",
    "EC2": "Amazon Elastic Compute Cloud - Compute",
    "ECR": "Amazon EC2 Container Registry (ECR)",
    "ECS": "Amazon EC2 Container Service",
    "EKS": "Amazon Elastic Container Service for Kubernetes",
    "EFS": "Amazon Elastic File System", "ELB": "Amazon Elastic Load Balancing",
    "ElastiCache": "Amazon ElastiCache", "Glue": "AWS Glue",
    "Lambda": "AWS Lambda", "RDS": "Amazon Relational Database Service",
    "Redshift": "Amazon Redshift", "Route53": "Amazon Route 53",
    "S3": "Amazon Simple Storage Service", "SES": "Amazon Simple Email Service",
    "SNS": "Amazon Simple Notification Service",
    "SQS": "Amazon Simple Queue Service", "VPC": "Amazon Virtual Private Cloud",
    "WAF": "AWS WAF", "KMS": "AWS Key Management Service",
    "CloudTrail": "AWS CloudTrail", "Config": "AWS Config",
    "SecretsManager": "AWS Secrets Manager", "SSM": "AWS Systems Manager",
    "SageMaker": "Amazon SageMaker", "Kinesis": "Amazon Kinesis",
    "CodeBuild": "AWS CodeBuild", "CodePipeline": "AWS CodePipeline",
    "Tax": "Tax", "Support": "AWS Support",
}
REVERSE = {v: k for k, v in SERVICE_NAME_MAPPING.items()}


def short_name(svc):
    return REVERSE.get(svc, svc)


def compute_impact_score(val1, val2, total, alpha=0.7):
    if val1 < 0.01 and val2 < 0.01:
        return 0.0
    delta = val2 - val1
    contrib = abs(delta / total) if total > 0 else 0.0
    pct = abs(delta / max(val1, 0.01))
    return alpha * contrib + (1 - alpha) * pct


def top_services(svc1, svc2, total2, n=5):
    all_svcs = set(svc1) | set(svc2)
    sig = [s for s in all_svcs
           if abs(svc2.get(s, 0) - svc1.get(s, 0)) >= 0.5
           and svc2.get(s, 0) >= 5.0]
    scores = {s: compute_impact_score(svc1.get(s, 0), svc2.get(s, 0), total2) for s in sig}
    return sorted(scores, key=scores.get, reverse=True)[:n]


def forecast_chart(forecast, benchmark, last_month):
    fig, ax = plt.subplots(figsize=(8, 4))
    labels = ["Last Month", "Forecast"]
    values = [float(last_month), float(forecast)]
    fc_color = "#DF362D" if forecast > benchmark else "#76B947"
    bars = ax.bar(labels, values, color=["#004369", fc_color], width=0.5)
    ax.axhline(y=benchmark, color="#FEDE00", linestyle=(0, (5, 1)), linewidth=1.8, label="Benchmark")
    ax.text(1.3, benchmark, f"${benchmark:,.0f}", color="#211522", fontsize=9, va="bottom")
    ax.set_ylabel("Cost (USD)")
    ax.set_title("Forecast vs Last Month")
    ax.set_ylim(0, max(values + [benchmark]) * 1.2)
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"${h:,.2f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 5), textcoords="offset points", ha="center")
    ax.legend()
    fig.tight_layout()
    return fig


def services_chart(top_svcs, svc1, svc2, label1, label2, mode):
    labels = [short_name(s) for s in top_svcs]
    v1 = [svc1.get(s, 0) for s in top_svcs]
    v2 = [svc2.get(s, 0) for s in top_svcs]
    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(labels))
    w = 0.35
    ax.bar([i - w / 2 for i in x], v1, width=w, label=label1, color="#175873")
    ax.bar([i + w / 2 for i in x], v2, width=w, label=label2, color="#87ACA3")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=0, ha="right")
    ax.set_title(f"Top {len(top_svcs)} Services by {mode} Cost Impact")
    ax.set_ylabel("Cost (USD)")
    ax.legend()
    fig.tight_layout()
    return fig
