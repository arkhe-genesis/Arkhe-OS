import os

structure = {
    "SaaS Stack": {
        "Frontend": ["React", "NextJS", "Vue", "TailwindCSS", "Shadcn UI"],
        "Backend": ["NodeJS", "Django", "Laravel", "FastAPI", "Express"],
        "Database": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Supabase"],
        "Auth": ["Clerk", "Auth0", "Firebase Auth", "Supabase Auth", "NextAuth"],
        "Payments": ["Stripe", "Paddle", "Dodo Payments", "Lemon Squeezy", "Polar"],
        "Emails": ["Resend", "SendGrid", "Mailgun", "Postmark", "Amazon SES"],
        "Storage": ["AWS", "Cloudflare", "Google Cloud Storage", "Supabase Storage", "Uploadcare"],
        "Deployment": ["Vercel", "Netlify", "Railway", "Render", "AWS"],
        "Domains and DNS": ["Namecheap", "Hostinger", "Cloudflare DNS", "Google Domains", "SiteGround"],
        "Analytics": ["Google Analytics", "Plausible", "PostHog", "Mixpanel", "DataFast"],
        "Monitoring": ["Sentry", "LogRocket", "Datadog", "NewRelic", "UptimeRobot"],
        "DevOps": ["Docker", "Kubernetes", "GitHub Actions", "CI CD", "Terraform"],
        "Search": ["Algolia", "Meilisearch", "Elasticsearch", "Typesense", "OpenSearch"],
        "AI Integration": ["OpenAI API", "Anthropic API", "Replicate", "HuggingFace", "Gemini API"],
        "Integrations": ["Zapier", "Make", "n8n", "Pabbly", "Webhooks"],
        "Security": ["SSL", "Cloudflare", "WAF", "Rate Limiting", "Secrets Management"],
        "Marketing": ["Search Console", "Outrank", "Buffer", "Analytics", "Kit"],
        "Customer Support": ["Intercom", "Crisp", "Zendesk", "Tawk", "HelpScout"]
    }
}

def create_structure(base_path, struct):
    for key, value in struct.items():
        path = os.path.join(base_path, key)
        os.makedirs(path, exist_ok=True)
        if isinstance(value, dict):
            create_structure(path, value)
        elif isinstance(value, list):
            for item in value:
                os.makedirs(os.path.join(path, item), exist_ok=True)

if __name__ == "__main__":
    create_structure(".", structure)
    print("Directory structure created successfully.")
