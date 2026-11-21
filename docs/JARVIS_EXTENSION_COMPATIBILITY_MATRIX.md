# JARVIS OS — Extension Compatibility Matrix

| Module | Category | Resource Tier | Primary DB / Storage | Permissions Required | Target Route |
|:---|:---|:---:|:---|:---|:---|
| M18 Orchestrator | Core AI OS | MEDIUM | `data/jarvis_orchestrator.db` | `orchestrator:write`, `agent:execute` | `/orchestrator` |
| M19 Computer Assistant | Core AI OS | MEDIUM | `data/jarvis_computer_assistant.db` | `desktop:control`, `shell:execute` | `/computer-assistant` |
| M20 Conversational AI | Core AI OS | HEAVY | `data/jarvis_conversational_ai.db` | `voice:record`, `voice:synthesize` | `/conversational-ai` |
| M21 Browser Agent | Core AI OS | MEDIUM | `data/jarvis_browser_agent.db` | `browser:navigate`, `network:read` | `/browser-agent` |
| M22 Model Router | Core AI OS | LIGHTWEIGHT | `data/jarvis_model_router.db` | `models:route`, `api:admin` | `/model-router` |
| M23 Executive Assistant | Productivity | LIGHTWEIGHT | `data/jarvis_executive_assistant.db` | `assistant:read`, `assistant:write` | `/executive-assistant` |
| M24 Email & Calendar | Productivity | LIGHTWEIGHT | `data/jarvis_email_calendar.db` | `calendar:manage`, `email:send` | `/email-calendar` |
| M25 Meeting Assistant | Productivity | LIGHTWEIGHT | `data/jarvis_meeting_assistant.db` | `meeting:record`, `notes:write` | `/meeting-assistant` |
| M26 Project Autopilot | Engineering | MEDIUM | `data/jarvis_project_autopilot.db` | `project:plan`, `tasks:dispatch` | `/project-autopilot` |
| M27 GitHub CI/CD | DevOps | LIGHTWEIGHT | `data/jarvis_github_cicd.db` | `git:read`, `cicd:trigger` | `/github-cicd` |
| M28 Data Analyst | Analytics | MEDIUM | `data/jarvis_data_analyst.db` | `data:query`, `reports:generate` | `/data-analyst` |
| M29 File Manager | Productivity | LIGHTWEIGHT | `data/jarvis_file_manager.db` | `fs:read`, `fs:write` | `/file-manager` |
| M30 Smart Home | IoT Automation | LIGHTWEIGHT | `data/jarvis_smart_home.db` | `iot:read`, `iot:control` | `/smart-home` |
| M31 Robot Brain | Robotics | MEDIUM | `data/jarvis_robot_brain.db` | `robot:telemetry`, `robot:arm` | `/robot-brain` |
| M32 System Health | Observability | LIGHTWEIGHT | `data/jarvis_system_health.db` | `system:metrics:read` | `/system-health` |
| M33 Cybersecurity | Security | LIGHTWEIGHT | `data/jarvis_cybersecurity.db` | `security:audit:read`, `rules:write` | `/cybersecurity` |
| M34 Finance Manager | Finance | LIGHTWEIGHT | `data/jarvis_finance.db` | `finance:read`, `budget:write` | `/finance` |
| M35 Workflow Builder | Automation | LIGHTWEIGHT | `data/jarvis_workflows.db` | `workflow:create`, `workflow:run` | `/workflows` |
| M36 Screen Vision | Computer Vision | HEAVY | `data/jarvis_vision.db` | `screen:capture`, `vision:infer` | `/screen-vision` |
| M37 Cross-Device | Device Mesh | LIGHTWEIGHT | `data/jarvis_devices.db` | `device:pair`, `device:message` | `/cross-device` |
| M38 Skills Marketplace | Extensibility | LIGHTWEIGHT | `data/jarvis_marketplace.db` | `plugins:install`, `skills:manage` | `/marketplace` |
| M39 Backup & Recovery | Resilience | MEDIUM | `data/jarvis_backups.db` | `backup:create`, `restore:execute` | `/backups` |
| M40 Permissions Center | Governance | LIGHTWEIGHT | `data/jarvis_approvals.db` | `approval:manage`, `policy:write` | `/approvals` |
| M41 Notification Center| Notifications | LIGHTWEIGHT | `data/jarvis_notifications.db` | `notifications:send`, `channels:read` | `/notifications` |
| M42 Extension Manager | Management | LIGHTWEIGHT | `data/jarvis_extensions.db` | `extensions:manage`, `sdk:host` | `/extensions` |
