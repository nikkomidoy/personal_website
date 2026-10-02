# Career Site

A personal career website built with **Django 5.2 + Wagtail 7 CMS**. It deploys to **AWS** (ECS Fargate, RDS PostgreSQL, S3) through **GitHub Actions**.

Everything on the site is edited in the CMS at `/cms/`:

| Where in the CMS | What you edit |
|---|---|
| **Settings → Site profile** | Name, job title, location, email, LinkedIn/GitHub links, résumé PDF, footer |
| **Pages → Home** | Headline, summary, photo, work experience, education, skills, extra content blocks |
| **Pages → Home → add child** | `Standard page` (About, Contact…), `Blog index` → `Blog page`, `Project index` → `Project page` |

Pages appear in the top navigation when you tick **Promote → Show in menus**.

## Project layout

```
config/            settings (base / dev / production), urls, wsgi
core/              site-wide profile setting, StreamField blocks, health-check middleware
home/              HomePage (experience, education, skills) + StandardPage
blog/              BlogIndexPage, BlogPage
portfolio/         ProjectIndexPage, ProjectPage
templates/ static/ front-end
tests/             pytest suite
deploy/cloudformation.yml   all AWS infrastructure
.github/workflows/ci.yml    lint, tests (Postgres), Docker build, CloudFormation lint
.github/workflows/cd.yml    build → push to ECR → migrate → deploy to ECS
```

## Local development

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo      # optional placeholder content
python manage.py runserver
```

The site is at http://localhost:8000 and the CMS at http://localhost:8000/cms/.

Before you push, run the same checks CI runs:

```bash
ruff check . && ruff format --check . && pytest
```

To run the production-like stack (the same Docker image as AWS, with Postgres):

```bash
docker compose up --build
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py createsuperuser
```

## AWS architecture

```
Internet ─► ALB (HTTP / HTTPS with ACM) ─► ECS Fargate service "web" (gunicorn + WhiteNoise for static files)
                                              ├─► RDS PostgreSQL 17 (private to the app's security group)
                                              ├─► S3 bucket for media uploads (images, résumé)
                                              └─► Secrets Manager (Django SECRET_KEY, DB credentials)
GitHub Actions ─(OIDC, no stored keys)─► ECR + ECS
```

- There is no NAT gateway, to keep costs down. Tasks run in public subnets, but security groups only allow traffic from the load balancer, and the database only accepts the tasks.
- The ALB checks `/health/`. That path skips host validation and the SSL redirect.
- The database uses deletion protection and takes a snapshot on delete. The media bucket is retained when the stack is deleted.
- Expect roughly **$40–50/month** at the defaults (ALB ≈ $16, Fargate 0.5 vCPU/1 GB ≈ $18, RDS t4g.micro ≈ $12, plus small S3/logs costs). Prices vary by region.

## First deployment

You need the AWS CLI configured for an account where you can create IAM roles.

**1. Push this project to a GitHub repository.**

**2. Create the stack.** `DesiredCount=0` is needed because no image exists yet.

```bash
aws cloudformation deploy \
  --stack-name careersite \
  --template-file deploy/cloudformation.yml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides GitHubRepo=<owner>/<repo> DesiredCount=0
```

If your account already has the GitHub OIDC provider (`token.actions.githubusercontent.com`), add `CreateGitHubOIDCProvider=false`.

**3. Configure GitHub.** Go to *Settings → Environments*, create an environment named **`production`**, and add these **variables**:

| Variable | Value |
|---|---|
| `AWS_REGION` | e.g. `us-east-1` |
| `AWS_DEPLOY_ROLE_ARN` | the `GitHubDeployRoleArn` stack output |
| `STACK_NAME` | `careersite` (optional, this is the default) |
| `ECS_DESIRED_COUNT` | `1` (optional, this is the default) |

No secrets are needed: the workflow assumes the IAM role through OIDC. The role only trusts jobs that run in the `production` environment. You can add required reviewers to that environment if you want manual approval before each deploy.

**4. Push to `main`, or run the CD workflow by hand.** The workflow:
1. runs the full CI suite,
2. builds the image and pushes it to ECR, tagged with the commit SHA and `latest`,
3. registers a new task definition revision,
4. runs `manage.py migrate` as a one-off Fargate task and stops if it fails,
5. updates the service and waits for it to be stable (the circuit breaker rolls back failed deploys),
6. runs a smoke test against `/health/`.

**5. Create your CMS admin user** inside the running container. This needs the [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html):

```bash
TASK=$(aws ecs list-tasks --cluster careersite --service-name careersite --query 'taskArns[0]' --output text)
aws ecs execute-command --cluster careersite --task "$TASK" --container web --interactive \
  --command "python manage.py createsuperuser"
```

Then open the `SiteURL` stack output and add `/cms/`.

**6. Later stack updates.** Pass `DesiredCount=1` so CloudFormation doesn't scale the site back to zero:

```bash
aws cloudformation deploy --stack-name careersite --template-file deploy/cloudformation.yml \
  --capabilities CAPABILITY_NAMED_IAM --parameter-overrides DesiredCount=1
```

## Custom domain and HTTPS

1. Request an ACM certificate for your domain in the stack's region and validate it through DNS.
2. Update the stack with `DomainName=www.example.com CertificateArn=arn:aws:acm:...`. This adds an HTTPS listener and HTTP→HTTPS redirect, and sets `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` and secure cookies.
3. Point a CNAME, or a Route 53 alias, at the `LoadBalancerDNSName` output.
4. In the CMS, under **Settings → Sites**, set the hostname to your domain. This is optional because the default site serves every host.
5. Once HTTPS works, consider setting `SECURE_HSTS_SECONDS` in the task definition.

## Configuration

All production settings come from environment variables. [.env.example](.env.example) lists them all. On AWS, the CloudFormation task definition sets them, and the secrets are injected from Secrets Manager.

## Logs and troubleshooting

```bash
aws logs tail /ecs/careersite --follow
```
