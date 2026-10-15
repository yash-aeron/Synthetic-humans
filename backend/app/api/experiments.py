from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
import asyncio
import json
import csv
import io

from backend.app.database import get_db
from backend.app.models.experiment import Experiment
from backend.app.models.synthetic_user import SyntheticUser
from backend.app.models.trajectory import TrajectoryStep
from backend.app.models.metrics import ExperimentMetrics
from backend.app.models.finding import FrictionFinding, ExperimentComparison
from backend.app.schemas.experiment import ExperimentCreate, ExperimentRead, ExperimentRunRequest
from backend.app.schemas.synthetic_user import SyntheticUserRead, SyntheticUserDetail, TrajectoryStepRead
from backend.app.schemas.metrics import ExperimentMetricsRead, FrictionFindingRead, ExperimentComparisonRead, ExperimentDetailResponse
from backend.app.simulation.orchestrator import ExperimentOrchestrator
from backend.app.simulation.population import PopulationGenerator
from backend.app.analysis.reports import ExperimentComparator
from backend.app.browser.playwright_runner import browser_manager
from backend.app.simulation.events import event_bus

router = APIRouter(prefix="/experiments", tags=["experiments"])

@router.post("", response_model=ExperimentRead, status_code=201)
async def create_experiment(payload: ExperimentCreate, db: AsyncSession = Depends(get_db)):
    # Validate authorization confirmation
    if not payload.is_authorized:
        raise HTTPException(status_code=400, detail="Experiment owner authorization confirmation is required.")

    # Determine allowed origins
    target_origin = browser_manager.get_origin(payload.target_url)
    origins = payload.allowed_origins or [target_origin]

    experiment = Experiment(
        name=payload.name,
        target_url=payload.target_url,
        description=payload.description,
        population_size=payload.population_size,
        task_definition=payload.task_definition.model_dump(),
        population_distributions=payload.population_distributions,
        max_steps_per_user=payload.max_steps_per_user,
        max_duration_seconds=payload.max_duration_seconds,
        concurrency=payload.concurrency,
        random_seed=payload.random_seed,
        model_configuration=payload.model_configuration or {},
        status="CREATED",
        is_authorized=payload.is_authorized,
        allowed_origins=origins
    )
    db.add(experiment)
    await db.flush()

    # Pre-generate synthetic population
    users = PopulationGenerator.generate_population(
        experiment_id=experiment.id,
        population_size=experiment.population_size,
        custom_distributions=experiment.population_distributions,
        random_seed=experiment.random_seed,
        initial_goal=payload.task_definition.goal
    )
    db.add_all(users)
    await db.commit()
    await db.refresh(experiment)

    return experiment

@router.get("", response_model=List[ExperimentRead])
async def list_experiments(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Experiment)
        .options(selectinload(Experiment.synthetic_users))
        .order_by(desc(Experiment.created_at))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    experiments = result.scalars().all()

    # Annotate summary counts
    response = []
    for exp in experiments:
        users = exp.synthetic_users
        exp_dict = {
            "id": exp.id,
            "name": exp.name,
            "target_url": exp.target_url,
            "description": exp.description,
            "population_size": exp.population_size,
            "task_definition": exp.task_definition,
            "population_distributions": exp.population_distributions,
            "max_steps_per_user": exp.max_steps_per_user,
            "max_duration_seconds": exp.max_duration_seconds,
            "concurrency": exp.concurrency,
            "random_seed": exp.random_seed,
            "model_configuration": exp.model_configuration,
            "status": exp.status,
            "is_authorized": exp.is_authorized,
            "allowed_origins": exp.allowed_origins,
            "created_at": exp.created_at,
            "started_at": exp.started_at,
            "completed_at": exp.completed_at,
            "completed_users_count": sum(1 for u in users if u.status == "COMPLETED"),
            "abandoned_users_count": sum(1 for u in users if u.status == "ABANDONED"),
            "failed_users_count": sum(1 for u in users if u.status in ("FAILED", "TIMEOUT"))
        }
        response.append(ExperimentRead(**exp_dict))

    return response

@router.get("/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Experiment)
        .options(
            selectinload(Experiment.synthetic_users),
            selectinload(Experiment.metrics),
            selectinload(Experiment.findings)
        )
        .where(Experiment.id == experiment_id)
    )
    result = await db.execute(stmt)
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")

    users = exp.synthetic_users
    exp_read = ExperimentRead(
        id=exp.id,
        name=exp.name,
        target_url=exp.target_url,
        description=exp.description,
        population_size=exp.population_size,
        task_definition=exp.task_definition,
        population_distributions=exp.population_distributions,
        max_steps_per_user=exp.max_steps_per_user,
        max_duration_seconds=exp.max_duration_seconds,
        concurrency=exp.concurrency,
        random_seed=exp.random_seed,
        model_configuration=exp.model_configuration,
        status=exp.status,
        is_authorized=exp.is_authorized,
        allowed_origins=exp.allowed_origins,
        created_at=exp.created_at,
        started_at=exp.started_at,
        completed_at=exp.completed_at,
        completed_users_count=sum(1 for u in users if u.status == "COMPLETED"),
        abandoned_users_count=sum(1 for u in users if u.status == "ABANDONED"),
        failed_users_count=sum(1 for u in users if u.status in ("FAILED", "TIMEOUT"))
    )

    metrics_read = ExperimentMetricsRead.model_validate(exp.metrics) if exp.metrics else None
    findings_read = [FrictionFindingRead.model_validate(f) for f in exp.findings]

    return ExperimentDetailResponse(
        experiment=exp_read,
        metrics=metrics_read,
        findings=findings_read
    )

@router.post("/{experiment_id}/run")
async def run_experiment(
    experiment_id: str,
    payload: Optional[ExperimentRunRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Experiment).where(Experiment.id == experiment_id)
    res = await db.execute(stmt)
    exp = res.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")

    if exp.status == "RUNNING":
        return {"status": "ALREADY_RUNNING", "experiment_id": experiment_id}

    concurrency = payload.concurrency if payload else exp.concurrency

    # Launch background job
    await ExperimentOrchestrator.start_experiment(experiment_id, concurrency=concurrency)

    return {
        "status": "QUEUED",
        "experiment_id": experiment_id,
        "concurrency": concurrency,
        "message": "Simulation job launched in background."
    }

@router.post("/{experiment_id}/cancel")
async def cancel_experiment(experiment_id: str):
    await ExperimentOrchestrator.cancel_experiment(experiment_id)
    return {"status": "CANCELLED", "experiment_id": experiment_id}

@router.get("/{experiment_id}/users", response_model=List[SyntheticUserRead])
async def list_experiment_users(
    experiment_id: str,
    status: Optional[str] = None,
    technical_proficiency: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SyntheticUser).where(SyntheticUser.experiment_id == experiment_id)
    if status:
        stmt = stmt.where(SyntheticUser.status == status)
    if technical_proficiency:
        stmt = stmt.where(SyntheticUser.technical_proficiency == technical_proficiency)

    stmt = stmt.order_by(SyntheticUser.created_at).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{experiment_id}/users/{user_id}", response_model=SyntheticUserDetail)
async def get_user_detail(
    experiment_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(SyntheticUser)
        .options(selectinload(SyntheticUser.trajectories))
        .where(SyntheticUser.experiment_id == experiment_id, SyntheticUser.id == user_id)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Synthetic user not found.")
    return user

@router.get("/{experiment_id}/metrics", response_model=ExperimentMetricsRead)
async def get_experiment_metrics(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ExperimentMetrics).where(ExperimentMetrics.experiment_id == experiment_id)
    res = await db.execute(stmt)
    metrics = res.scalar_one_or_none()
    if not metrics:
        raise HTTPException(status_code=404, detail="Metrics not yet computed for this experiment.")
    return metrics

@router.get("/{experiment_id}/findings", response_model=List[FrictionFindingRead])
async def get_experiment_findings(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(FrictionFinding).where(FrictionFinding.experiment_id == experiment_id)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{experiment_id}/compare/{variant_id}", response_model=ExperimentComparisonRead)
async def compare_experiments(
    experiment_id: str,
    variant_id: str,
    db: AsyncSession = Depends(get_db)
):
    base_m_stmt = select(ExperimentMetrics).where(ExperimentMetrics.experiment_id == experiment_id)
    var_m_stmt = select(ExperimentMetrics).where(ExperimentMetrics.experiment_id == variant_id)

    base_m = (await db.execute(base_m_stmt)).scalar_one_or_none()
    var_m = (await db.execute(var_m_stmt)).scalar_one_or_none()

    if not base_m or not var_m:
        raise HTTPException(status_code=400, detail="Both experiments must have completed metrics to be compared.")

    comparison = ExperimentComparator.compare(experiment_id, variant_id, base_m, var_m)
    return comparison

@router.get("/{experiment_id}/stream")
async def stream_experiment_events(experiment_id: str, db: AsyncSession = Depends(get_db)):
    """Server-Sent Events (SSE) live simulation telemetry stream."""
    stmt = select(Experiment.id).where(Experiment.id == experiment_id)
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Experiment not found.")

    async def event_generator():
        q = await event_bus.subscribe(experiment_id)
        try:
            yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'experiment_id': experiment_id})}\n\n"
            while True:
                try:
                    event_data = await asyncio.wait_for(q.get(), timeout=12.0)
                    evt_type = event_data.get("type", "message")
                    yield f"event: {evt_type}\ndata: {json.dumps(event_data)}\n\n"
                    if evt_type == "experiment_finish":
                        break
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            await event_bus.unsubscribe(experiment_id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/{experiment_id}/export/json")
async def export_experiment_json(experiment_id: str, db: AsyncSession = Depends(get_db)):
    """Exports entire experiment, synthetic population, trajectories, metrics, and findings as structured JSON."""
    stmt = (
        select(Experiment)
        .options(
            selectinload(Experiment.synthetic_users).selectinload(SyntheticUser.trajectories),
            selectinload(Experiment.metrics),
            selectinload(Experiment.findings)
        )
        .where(Experiment.id == experiment_id)
    )
    res = await db.execute(stmt)
    exp = res.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")

    export_data = {
        "export_metadata": {
            "platform": "Synthetic Humans",
            "version": "1.0.0"
        },
        "experiment": {
            "id": exp.id,
            "name": exp.name,
            "target_url": exp.target_url,
            "description": exp.description,
            "status": exp.status,
            "population_size": exp.population_size,
            "task_definition": exp.task_definition,
            "population_distributions": exp.population_distributions,
            "random_seed": exp.random_seed,
            "max_steps_per_user": exp.max_steps_per_user,
            "max_duration_seconds": exp.max_duration_seconds,
            "created_at": exp.created_at.isoformat() if exp.created_at else None,
            "started_at": exp.started_at.isoformat() if exp.started_at else None,
            "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
        },
        "metrics": {
            "task_completion_rate": exp.metrics.task_completion_rate if exp.metrics else None,
            "task_abandonment_rate": exp.metrics.task_abandonment_rate if exp.metrics else None,
            "average_task_duration": exp.metrics.average_task_duration if exp.metrics else None,
            "median_task_duration": exp.metrics.median_task_duration if exp.metrics else None,
            "p95_task_duration": exp.metrics.p95_task_duration if exp.metrics else None,
            "average_actions": exp.metrics.average_actions if exp.metrics else None,
            "average_errors": exp.metrics.average_errors if exp.metrics else None,
            "retry_rate": exp.metrics.retry_rate if exp.metrics else None,
            "confusion_rate": exp.metrics.confusion_rate if exp.metrics else None,
            "segment_metrics": exp.metrics.segment_metrics if exp.metrics else {},
            "funnel_steps": exp.metrics.funnel_steps if exp.metrics else [],
            "heatmap_data": exp.metrics.heatmap_data if exp.metrics else []
        } if exp.metrics else None,
        "findings": [
            {
                "id": f.id,
                "severity": f.severity,
                "category": f.category,
                "title": f.title,
                "description": f.description,
                "evidence": f.evidence,
                "recommendation": f.recommendation
            }
            for f in exp.findings
        ],
        "synthetic_users": [
            {
                "id": u.id,
                "technical_proficiency": u.technical_proficiency,
                "patience": u.patience,
                "risk_tolerance": u.risk_tolerance,
                "reading_behavior": u.reading_behavior,
                "status": u.status,
                "steps_taken": u.steps_taken,
                "duration_seconds": u.duration_seconds,
                "error_count": u.error_count,
                "frustration_level": u.frustration_level,
                "confidence_level": u.confidence_level,
                "trajectories": [
                    {
                        "step_number": t.step_number,
                        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                        "url": t.url,
                        "page_title": t.page_title,
                        "action_type": t.action_type,
                        "action_target": t.action_target,
                        "action_parameters": t.action_parameters,
                        "action_reason": t.action_reason,
                        "action_confidence": t.action_confidence,
                        "action_result": t.action_result,
                        "latency_ms": t.latency_ms,
                        "frustration_after": t.frustration_after,
                        "error_message": t.error_message,
                        "screenshot_path": t.screenshot_path
                    }
                    for t in u.trajectories
                ]
            }
            for u in exp.synthetic_users
        ]
    }

    content = json.dumps(export_data, indent=2, default=str)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=experiment-{experiment_id}-export.json"}
    )

@router.get("/{experiment_id}/export/csv")
async def export_experiment_csv(experiment_id: str, db: AsyncSession = Depends(get_db)):
    """Exports raw step-by-step trajectory events as a CSV spreadsheet."""
    stmt = (
        select(TrajectoryStep, SyntheticUser.technical_proficiency)
        .join(SyntheticUser, TrajectoryStep.synthetic_user_id == SyntheticUser.id)
        .where(TrajectoryStep.experiment_id == experiment_id)
        .order_by(TrajectoryStep.synthetic_user_id, TrajectoryStep.step_number)
    )
    res = await db.execute(stmt)
    rows = res.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "experiment_id",
        "user_id",
        "technical_proficiency",
        "step_number",
        "timestamp",
        "url",
        "action_type",
        "action_target",
        "action_result",
        "latency_ms",
        "frustration_after",
        "confidence_after",
        "action_confidence",
        "error_message",
        "action_reason"
    ])

    for step, prof in rows:
        writer.writerow([
            step.experiment_id,
            step.synthetic_user_id,
            prof,
            step.step_number,
            step.timestamp.isoformat() if step.timestamp else "",
            step.url,
            step.action_type,
            step.action_target,
            step.action_result,
            step.latency_ms,
            step.frustration_after,
            step.confidence_after,
            step.action_confidence,
            step.error_message or "",
            step.action_reason.replace("\n", " ") if step.action_reason else ""
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=experiment-{experiment_id}-events.csv"}
    )

@router.get("/{experiment_id}/export/report")
async def export_experiment_report(experiment_id: str, db: AsyncSession = Depends(get_db)):
    """Generates an executive Usability & HCI Audit Report in Markdown."""
    stmt = (
        select(Experiment)
        .options(
            selectinload(Experiment.synthetic_users),
            selectinload(Experiment.metrics),
            selectinload(Experiment.findings)
        )
        .where(Experiment.id == experiment_id)
    )
    res = await db.execute(stmt)
    exp = res.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")

    m = exp.metrics
    users = exp.synthetic_users

    doc = [
        f"# Synthetic Humans - Usability & Behavioral Audit Report",
        f"**Experiment Name:** {exp.name}",
        f"**Experiment ID:** `{exp.id}`",
        f"**Target Application:** [{exp.target_url}]({exp.target_url})",
        f"**Task Goal:** \"{exp.task_definition.get('goal', 'N/A')}\"",
        f"**Population Tested:** {exp.population_size} persistent synthetic agents",
        f"**Status:** {exp.status} | **Completed At:** {exp.completed_at or 'In Progress'}\n",
        f"---",
        f"## 1. Executive Summary",
        f"Synthetic Humans deployed a simulated population of {exp.population_size} autonomous, cognitive agents modeled after distinct human behavioral archetypes. Agents navigated the target application with persistent psychological state tracking (frustration, confidence, visual attention).",
        f"- **Task Completion Rate:** {round((m.task_completion_rate * 100) if m else 0)}%",
        f"- **Task Abandonment Rate:** {round((m.task_abandonment_rate * 100) if m else 0)}%",
        f"- **Average Duration:** {m.average_task_duration if m else 0}s (Median: {m.median_task_duration if m else 0}s, p95: {m.p95_task_duration if m else 0}s)",
        f"- **Confusion / Loop Rate:** {round((m.confusion_rate * 100) if m else 0)}%\n",
        f"| Metric | Value | Baseline Standard | Status |",
        f"| :--- | :--- | :--- | :--- |",
        f"| Completion Rate | {round((m.task_completion_rate * 100) if m else 0)}% | >= 80% | {'[PASS]' if (m and m.task_completion_rate >= 0.8) else '[NEEDS WORK]'} |",
        f"| Abandonment Rate | {round((m.task_abandonment_rate * 100) if m else 0)}% | <= 15% | {'[PASS]' if (m and m.task_abandonment_rate <= 0.15) else '[HIGH]'} |",
        f"| Avg Actions to Goal | {m.average_actions if m else 0} | <= 10 | {'[OPTIMAL]' if (m and m.average_actions <= 10) else '[ELEVATED]'} |",
        f"| Navigation Loops / Confusion | {round((m.confusion_rate * 100) if m else 0)}% | <= 10% | {'[OPTIMAL]' if (m and m.confusion_rate <= 0.10) else '[HIGH]'} |\n",
        f"---",
        f"## 2. Detected Usability Friction Findings",
    ]

    if not exp.findings:
        doc.append("No critical usability friction anomalies detected.\n")
    else:
        for idx, f in enumerate(exp.findings, 1):
            doc.extend([
                f"### {idx}. [{f.severity}] {f.title}",
                f"- **Category:** `{f.category}`",
                f"- **Observed Phenomenon:** {f.description}",
                f"- **Behavioral Recommendation:** {f.recommendation}\n"
            ])

    if m and m.segment_metrics:
        doc.extend([
            f"---",
            f"## 3. Behavioral Cohort Breakdown",
            f"| Technical Proficiency | Agents | Completed | Completion Rate | Avg Duration | Avg Frustration |",
            f"| :--- | :--- | :--- | :--- | :--- | :--- |"
        ])
        for prof, seg in (m.segment_metrics.get("technical_proficiency", {})).items():
            doc.append(f"| {prof} | {seg.get('total')} | {seg.get('completed')} | {round(seg.get('completion_rate', 0)*100)}% | {seg.get('avg_duration')}s | {seg.get('avg_frustration')} |")
        doc.append("")

    if m and m.funnel_steps:
        doc.extend([
            f"---",
            f"## 4. Conversion Funnel Drop-off",
            f"| Funnel Stage | Reached | Conversion Rate |",
            f"| :--- | :--- | :--- |"
        ])
        for step in m.funnel_steps:
            doc.append(f"| {step.get('stage')} | {step.get('users_reached')} | {round(step.get('conversion_rate', 0)*100)}% |")
        doc.append("")

    doc.extend([
        f"---",
        f"## 5. Methodology & Cognitive Physics Engine",
        f"Synthetic Humans evaluates web applications by orchestrating autonomous agents running in isolated browser sandboxes.",
        f"Cognitive latency is computed via the Hick-Hyman law, visual scanning simulates human reading patterns (F-pattern / scanning / thorough), and frustration builds dynamically upon repeated action failures, circular navigation loops, or confusing form validation responses."
    ])

    report_content = "\n".join(doc)
    return Response(
        content=report_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=usability-audit-report-{experiment_id}.md"}
    )
