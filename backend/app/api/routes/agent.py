"""Agent control endpoints."""

import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from loguru import logger

from app.database.session import get_db, get_db_session
from app.database.models import AgentConfig

router = APIRouter()


class AgentStatusResponse(BaseModel):
    """Agent status response model."""

    state: str
    polling_interval_seconds: int
    max_concurrent_fixes: int
    require_approval: bool
    dry_run_mode: bool


class AgentUpdateRequest(BaseModel):
    """Agent configuration update request."""

    state: str | None = None
    polling_interval_seconds: int | None = None
    max_concurrent_fixes: int | None = None
    require_approval: bool | None = None
    dry_run_mode: bool | None = None


@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status(db: AsyncSession = Depends(get_db)):
    """
    Get current agent status and configuration.

    Returns:
        Current agent state and settings
    """
    # Get agent config (should be only one row)
    result = await db.execute(select(AgentConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        # Create default config if not exists
        config = AgentConfig(
            state="stopped",
            polling_interval_seconds=300,
            max_concurrent_fixes=1,
            require_approval=True,
            dry_run_mode=True,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return AgentStatusResponse(
        state=config.state,
        polling_interval_seconds=config.polling_interval_seconds,
        max_concurrent_fixes=config.max_concurrent_fixes,
        require_approval=config.require_approval,
        dry_run_mode=config.dry_run_mode,
    )


@router.post("/start")
async def start_agent(db: AsyncSession = Depends(get_db)):
    """
    Start the AI Agent.

    Returns:
        Success message and new state
    """
    from ...agent.background_service import agent_service

    result = await db.execute(select(AgentConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")

    if config.state == "running" and agent_service.is_running:
        return {"message": "Agent is already running", "state": "running"}

    # Update database state
    config.state = "running"
    await db.commit()

    # Start the actual agent service
    try:
        logger.info("Starting agent service...")
        await agent_service.start()
        logger.info("Agent started successfully")
        return {"message": "Agent started successfully", "state": "running"}
    except Exception as e:
        logger.exception(f"Failed to start agent: {e}")
        config.state = "stopped"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to start agent: {str(e)}")


@router.post("/stop")
async def stop_agent(db: AsyncSession = Depends(get_db)):
    """
    Stop the AI Agent.

    Returns:
        Success message and new state
    """
    from ...agent.background_service import agent_service

    result = await db.execute(select(AgentConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")

    if config.state == "stopped" and not agent_service.is_running:
        return {"message": "Agent is already stopped", "state": "stopped"}

    # Stop the actual agent service
    try:
        await agent_service.stop()
        logger.info("Agent stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping agent: {e}")

    # Update database state
    config.state = "stopped"
    await db.commit()

    return {"message": "Agent stopped successfully", "state": "stopped"}


@router.post("/pause")
async def pause_agent(db: AsyncSession = Depends(get_db)):
    """
    Pause the AI Agent.

    Returns:
        Success message and new state
    """
    result = await db.execute(select(AgentConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")

    if config.state != "running":
        raise HTTPException(status_code=400, detail="Agent must be running to pause")

    config.state = "paused"
    await db.commit()

    logger.info("Agent paused")
    return {"message": "Agent paused successfully", "state": "paused"}


@router.patch("/config")
async def update_agent_config(
    updates: AgentUpdateRequest, db: AsyncSession = Depends(get_db)
):
    """
    Update agent configuration.

    Args:
        updates: Configuration fields to update

    Returns:
        Updated configuration
    """
    result = await db.execute(select(AgentConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")

    # Update only provided fields
    update_data = updates.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    logger.info(f"Agent config updated: {update_data}")

    return AgentStatusResponse(
        state=config.state,
        polling_interval_seconds=config.polling_interval_seconds,
        max_concurrent_fixes=config.max_concurrent_fixes,
        require_approval=config.require_approval,
        dry_run_mode=config.dry_run_mode,
    )


@router.get("/stats")
async def get_agent_stats(db: AsyncSession = Depends(get_db)):
    """
    Get agent statistics.

    Returns:
        Statistics about agent activity
    """
    # TODO: Calculate real stats from database
    return {
        "total_errors_detected": 0,
        "total_fixes_applied": 0,
        "success_rate": 0.0,
        "fixes_today": 0,
        "pending_approvals": 0,
        "uptime_hours": 0,
    }


@router.get("/scan/{scan_id}/progress")
async def get_scan_progress(scan_id: str):
    """
    Get progress of a running scan.

    Args:
        scan_id: Scan ID from /scan endpoint

    Returns:
        Progress information with percentage
    """
    from app.services.progress_tracker import progress_tracker

    progress = progress_tracker.get_progress(scan_id)

    if not progress:
        raise HTTPException(
            status_code=404,
            detail="Scan not found"
        )

    return progress


@router.get("/results")
async def get_scan_results(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent scan results (errors found).

    Args:
        limit: Number of results to return
        offset: Offset for pagination

    Returns:
        List of errors with driver and company info
    """
    from sqlalchemy import desc
    from app.database.models import Error

    result = await db.execute(
        select(Error)
        .order_by(desc(Error.discovered_at))
        .limit(limit)
        .offset(offset)
    )
    errors = result.scalars().all()

    return {
        "total": len(errors),
        "errors": [
            {
                "id": str(error.id),
                "driver_id": error.driver_id,
                "driver_name": error.driver_name,
                "company_id": error.company_id,
                "company_name": error.company_name,
                "error_key": error.error_key,
                "error_name": error.error_name,
                "error_message": error.error_message,
                "severity": error.severity,
                "category": error.category,
                "status": error.status,
                "discovered_at": error.discovered_at.isoformat() if error.discovered_at else None,
            }
            for error in errors
        ]
    }


class ScanRequest(BaseModel):
    """Scan request model."""

    company_id: str | None = None
    driver_ids: list[str] | None = None
    scan_all: bool = False
    scan_logs: bool = False  # Если True, будет сканировать логи через Playwright


@router.post("/scan")
async def trigger_scan(
    request: ScanRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger Smart Analyze scan for selected companies/drivers.

    This will launch the demo agent to scan logs and detect errors.

    Args:
        request: Scan request with company_id, driver_ids, or scan_all flag

    Returns:
        Scan status and job ID
    """
    from app.services.scanner_service import scanner_service
    import asyncio

    logger.info(f"Scan requested: company_id={request.company_id!r} driver_ids={request.driver_ids!r} scan_all={request.scan_all}")

    # Требуется либо company_id, либо driver_ids
    if not request.company_id and not request.driver_ids:
        raise HTTPException(
            status_code=400,
            detail="Необходимо указать company_id или driver_ids"
        )

    # Если выбрана компания без водителей - получим всех водителей этой компании
    driver_ids_to_scan = request.driver_ids if request.driver_ids else []
    company_data = None
    company_name = None

    if request.company_id and not driver_ids_to_scan:
        # Получаем всех водителей компании через Fortex API
        try:
            from app.fortex.client import FortexAPIClient
            from app.config import get_settings

            settings = get_settings()
            fortex_client = FortexAPIClient(
                base_url=settings.fortex_api_url,
                auth_token=settings.fortex_auth_token
            )

            # Get company name from monitoring overview
            try:
                overview = await fortex_client.get_monitoring_overview()
                for comp in overview.companies:
                    if comp.id == request.company_id:
                        company_name = comp.name
                        break
            except Exception as e:
                logger.warning(f"Не удалось получить имя компании: {e}")

            logger.info(f"Получение всех водителей для компании {request.company_id} ({company_name or 'Неизвестная компания'})")
            smart_analyze = await fortex_client.get_smart_analyze(request.company_id)

            # Извлекаем driver_id из каждого DriverLog
            driver_ids_to_scan = [
                driver.driver_id or driver.driverId
                for driver in smart_analyze.drivers
                if driver.driver_id or driver.driverId
            ]

            logger.info(f"Найдено {len(driver_ids_to_scan)} водителей в компании")

            # Save the smart_analyze data for later use
            company_data = smart_analyze
            # Add company name to response
            if company_name:
                company_data.company_name = company_name

            await fortex_client.close()

            if not driver_ids_to_scan:
                raise HTTPException(
                    status_code=404,
                    detail=f"В компании не найдено водителей с ошибками"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Ошибка получения водителей компании: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Не удалось получить список водителей: {str(e)}"
            )

    # Generate scan ID
    import uuid
    scan_id = str(uuid.uuid4())

    # Enrich names from Supabase FIRST (before progress tracker to avoid stuck "running" status)
    from app.supabase.client import get_supabase_client
    supabase = get_supabase_client()

    try:
        companies = await supabase.get_companies_with_drivers()
        # Build lookup maps
        company_names_map = {c.company_id: c.company_name for c in companies}
        driver_names_map = {}
        for company in companies:
            for driver in company.drivers:
                driver_names_map[driver.driver_id] = driver.driver_name

        # Update company_name if we have it
        if request.company_id and request.company_id in company_names_map:
            company_name = company_names_map[request.company_id]
            logger.info(f"Enriched company name from Supabase: {company_name}")
    except Exception as e:
        logger.warning(f"Failed to enrich names from Supabase: {e}")
        company_names_map = {}
        driver_names_map = {}

    # CRITICAL: If log scanning is enabled, validate company_name is set BEFORE starting progress tracker
    # This prevents wrong company selection in Playwright automation AND avoids stuck "running" status
    if request.scan_logs and request.company_id and not company_name:
        logger.error(f"❌ Cannot start scan with logs: company_name is None for company_id={request.company_id}")
        raise HTTPException(
            status_code=400,
            detail=f"Company name could not be resolved for ID {request.company_id}. Please refresh and try again."
        )

    # NOW it's safe to initialize progress tracking (all validation passed)
    from app.services.progress_tracker import progress_tracker
    progress_tracker.start_scan(scan_id, len(driver_ids_to_scan))

    # Capture variables for closure
    _company_data = company_data
    _company_name = company_name
    _driver_ids = driver_ids_to_scan
    _company_id = request.company_id
    _scan_logs = request.scan_logs
    _driver_names_map = driver_names_map

    # Run scan in background
    async def run_scan_in_background():
        """Run scan without blocking the response."""
        try:
            # Очищаем старые ошибки для сканируемых водителей
            try:
                from app.database.models import Error
                from app.database.session import get_db_session
                from sqlalchemy import delete

                async with get_db_session() as db_session:
                    del_result = await db_session.execute(
                        delete(Error).where(Error.driver_id.in_(_driver_ids))
                    )
                    await db_session.commit()
                    deleted_count = del_result.rowcount
                    if deleted_count > 0:
                        logger.info(f"🗑️ Удалено {deleted_count} старых ошибок для {len(_driver_ids)} водителей перед новым сканом")
            except Exception as cleanup_err:
                logger.warning(f"⚠️ Не удалось очистить старые ошибки: {cleanup_err}")

            # Этап 1: Smart Analyze (with enriched names from Supabase)
            progress_tracker.update_message(scan_id, "Запуск Smart Analyze...")
            logger.info(f"Starting scan with enriched names: company_name={_company_name}, driver_names_map keys={list(_driver_names_map.keys())[:3]}")
            result = await scanner_service.scan_drivers(
                driver_ids=_driver_ids,
                company_id=_company_id,
                scan_id=scan_id,
                company_data=_company_data if _company_id else None,
                driver_names_map=_driver_names_map,
                company_name=_company_name
            )
            logger.info(f"Smart Analyze completed with enriched names: success={result.get('success')}, total_errors={result.get('total_errors_found')}")

            # Этап 2: Сканирование логов (если включено)
            if _scan_logs:
                progress_tracker.update_message(scan_id, "Запуск сканирования логов...")
                from app.services.log_scanner_service import LogScannerService

                log_scanner = LogScannerService()
                log_results = []

                try:
                    for idx, driver_id in enumerate(_driver_ids):
                        progress_tracker.update_driver(scan_id, idx, driver_id)
                        progress_tracker.update_message(scan_id, f"Сканирование логов драйвера {idx + 1}/{len(_driver_ids)}...")

                        # Get driver name from Supabase map (prioritize) or Smart Analyze
                        driver_name = _driver_names_map.get(driver_id)
                        if not driver_name and _company_data:
                            for driver_log in _company_data.drivers:
                                if (driver_log.driver_id == driver_id or driver_log.driverId == driver_id):
                                    driver_name = driver_log.driver_name
                                    break

                        # Сканируем логи через Playwright
                        log_result = await log_scanner.scan_driver_logs(
                            driver_id=driver_id,
                            driver_name=driver_name,
                            company_name=_company_name,
                            company_id=_company_id,
                            scan_id=scan_id
                        )
                        log_results.append(log_result)

                        if log_result.get('success'):
                            logger.info(f"Логи драйвера {driver_id[:8]}: {log_result.get('total_logs', 0)} записей, {log_result.get('issues_found', 0)} проблем")
                        else:
                            # Сохраняем ошибку сканирования в БД для отображения в Results
                            error_msg = log_result.get('error', 'Unknown error')
                            logger.error(f"Failed to scan driver {driver_id[:8]}: {error_msg}")
                            try:
                                from app.database.models import Error
                                from app.database.session import get_db_session

                                async with get_db_session() as db_session:
                                    scan_error = Error(
                                        driver_id=driver_id,
                                        driver_name=driver_name or f'Driver {driver_id[:8]}',
                                        company_id=_company_id or 'unknown',
                                        company_name=_company_name or 'Unknown Company',
                                        error_key='scan_failed',
                                        error_name='Ошибка сканирования',
                                        error_message=f"Не удалось просканировать драйвера: {error_msg}",
                                        severity='high',
                                        category='diagnostic',
                                        status='failed',
                                        error_metadata={'scan_error': error_msg, 'scan_id': scan_id},
                                        discovered_at=datetime.utcnow()
                                    )
                                    db_session.add(scan_error)
                                    await db_session.commit()
                            except Exception as save_err:
                                logger.error(f"❌ Не удалось сохранить ошибку сканирования: {save_err}")

                    result['log_scan_results'] = log_results
                    result['total_logs_scanned'] = sum(r.get('total_logs', 0) for r in log_results if r.get('success'))
                    result['total_log_issues'] = sum(r.get('issues_found', 0) for r in log_results if r.get('success'))

                finally:
                    await log_scanner.cleanup()

            progress_tracker.complete_scan(scan_id, success=result.get('success', False))
            logger.info(f"Полное сканирование завершено: {result}")
        except Exception as e:
            logger.exception(f"Сканирование провалилось: {e}")
            progress_tracker.complete_scan(scan_id, success=False, message=f"Ошибка: {str(e)}")

    # Start background task
    asyncio.create_task(run_scan_in_background())

    return {
        "status": "started",
        "scan_id": scan_id,
        "message": f"Scan initiated for {len(driver_ids_to_scan)} drivers",
        "driver_count": len(driver_ids_to_scan),
        "company_id": request.company_id,
    }


@router.post("/scan-logs")
async def scan_logs_only(
    request: ScanRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Scan driver logs using Playwright (without Smart Analyze).

    Args:
        request: Scan request with company_id or driver_ids

    Returns:
        Scan status and job ID
    """
    logger.info(f"Log scan requested: company_id={request.company_id!r} driver_ids={request.driver_ids!r}")

    if not request.company_id and not request.driver_ids:
        raise HTTPException(
            status_code=400,
            detail="Необходимо указать company_id или driver_ids"
        )

    # Получаем список драйверов
    driver_ids_to_scan = request.driver_ids if request.driver_ids else []
    company_name = None
    company_data = None

    if request.company_id and not driver_ids_to_scan:
        # Получаем всех драйверов компании
        try:
            from app.fortex.client import FortexAPIClient
            from app.config import get_settings

            settings = get_settings()
            fortex_client = FortexAPIClient(
                base_url=settings.fortex_api_url,
                auth_token=settings.fortex_auth_token
            )

            # Get company name
            try:
                overview = await fortex_client.get_monitoring_overview()
                for comp in overview.companies:
                    if comp.id == request.company_id:
                        company_name = comp.name
                        break
            except Exception as e:
                logger.warning(f"Не удалось получить имя компании: {e}")

            # Get drivers
            smart_analyze = await fortex_client.get_smart_analyze(request.company_id)
            driver_ids_to_scan = [
                driver.driver_id or driver.driverId
                for driver in smart_analyze.drivers
                if driver.driver_id or driver.driverId
            ]

            company_data = smart_analyze
            if company_name:
                company_data.company_name = company_name

            await fortex_client.close()

            if not driver_ids_to_scan:
                raise HTTPException(
                    status_code=404,
                    detail=f"В компании не найдено водителей"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Ошибка получения водителей компании: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Не удалось получить список водителей: {str(e)}"
            )

    # Generate scan ID
    import uuid
    scan_id = str(uuid.uuid4())

    # Enrich names from Supabase FIRST - CRITICAL for company selection
    # Do this BEFORE starting progress tracker so validation errors don't leave scan stuck on "running"
    from app.supabase.client import get_supabase_client
    supabase = get_supabase_client()
    company_names_map = {}
    driver_names_map = {}

    try:
        companies = await supabase.get_companies_with_drivers()
        # Build lookup maps
        company_names_map = {c.company_id: c.company_name for c in companies}
        for company in companies:
            for driver in company.drivers:
                driver_names_map[driver.driver_id] = driver.driver_name

        logger.info(f"Supabase: loaded {len(company_names_map)} companies, looking for company_id={request.company_id}")

        # Update company_name from Supabase (MUST override any previous value)
        if request.company_id:
            if request.company_id in company_names_map:
                company_name = company_names_map[request.company_id]
                logger.info(f"✅ Enriched company name from Supabase: '{company_name}'")
            else:
                # Log first 5 company IDs to help debug
                sample_ids = list(company_names_map.keys())[:5]
                logger.error(f"❌ Company ID '{request.company_id}' NOT FOUND in Supabase! Sample IDs: {sample_ids}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Company ID {request.company_id} not found in database"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Failed to enrich names from Supabase: {e}")

    # CRITICAL: Validate company_name is set BEFORE starting progress tracker
    # This prevents scan from being stuck on "running" if validation fails
    if request.company_id and not company_name:
        logger.error(f"❌ Cannot start scan: company_name is None for company_id={request.company_id}")
        raise HTTPException(
            status_code=400,
            detail=f"Company name could not be resolved for ID {request.company_id}. Please refresh and try again."
        )

    # Capture variables BEFORE starting progress tracker
    _company_data = company_data
    _company_name = company_name
    _company_id = request.company_id
    _driver_ids = driver_ids_to_scan
    _driver_names_map = driver_names_map

    logger.info(f"✅ Scan validated: company='{_company_name}', drivers={len(_driver_ids)}")

    # NOW it's safe to initialize progress tracking (all validation passed)
    from app.services.progress_tracker import progress_tracker
    progress_tracker.start_scan(scan_id, len(driver_ids_to_scan))

    # Run log scan in background
    async def run_log_scan_in_background():
        """Run log scan without blocking the response."""
        try:
            # Очищаем старые ошибки для сканируемых водителей
            try:
                from app.database.models import Error
                from app.database.session import get_db_session
                from sqlalchemy import delete

                async with get_db_session() as db_session:
                    del_result = await db_session.execute(
                        delete(Error).where(Error.driver_id.in_(_driver_ids))
                    )
                    await db_session.commit()
                    deleted_count = del_result.rowcount
                    if deleted_count > 0:
                        logger.info(f"🗑️ Удалено {deleted_count} старых ошибок для {len(_driver_ids)} водителей перед сканированием логов")
            except Exception as cleanup_err:
                logger.warning(f"⚠️ Не удалось очистить старые ошибки: {cleanup_err}")

            from app.services.log_scanner_service import LogScannerService

            progress_tracker.update_message(scan_id, "Запуск сканирования логов...")
            logger.info(f"Starting log scan: company_name={_company_name}, driver_count={len(_driver_ids)}")
            log_scanner = LogScannerService()
            log_results = []

            try:
                # Подготовка списка драйверов с именами
                drivers_to_scan = []
                for driver_id in _driver_ids:
                    # Get driver name from Supabase map (prioritize) or Smart Analyze
                    driver_name = _driver_names_map.get(driver_id)
                    if not driver_name and _company_data:
                        for driver_log in _company_data.drivers:
                            if (driver_log.driver_id == driver_id or driver_log.driverId == driver_id):
                                driver_name = driver_log.driver_name
                                break

                    drivers_to_scan.append({
                        'driver_id': driver_id,
                        'driver_name': driver_name or f"Driver {driver_id[:8]}"
                    })
                    logger.info(f"Prepared driver: {driver_id[:8]} ({driver_name or 'unknown'})")

                # Сканируем всех драйверов ПАРАЛЛЕЛЬНО (несколько вкладок одновременно)
                logger.info(f"Starting PARALLEL scan for {len(drivers_to_scan)} drivers, company={_company_name}")
                log_results = await log_scanner.scan_drivers_parallel(
                    drivers=drivers_to_scan,
                    company_name=_company_name,
                    company_id=_company_id,
                    scan_id=scan_id
                )

                # Логируем результаты и сохраняем в БД
                total_errors_saved = 0
                successful_drivers = 0
                failed_drivers = 0

                for log_result in log_results:
                    driver_id = log_result.get('driver_id', 'unknown')
                    if log_result.get('success'):
                        successful_drivers += 1
                        logger.info(f"Logs for driver {driver_id[:8]}: {log_result.get('total_logs', 0)} entries, {log_result.get('issues_found', 0)} issues")

                        # Сохраняем найденные ошибки в БД
                        issues = log_result.get('issues', [])
                        if issues:
                            try:
                                from app.database.models import Error
                                from app.database.session import get_db_session

                                async with get_db_session() as db_session:
                                    for issue in issues:
                                        # Создаем запись об ошибке
                                        error_record = Error(
                                            driver_id=driver_id,
                                            driver_name=log_result.get('driver_name'),
                                            company_id=_company_id or 'unknown',
                                            company_name=_company_name or 'Unknown Company',
                                            error_key=issue.get('error_type', 'unknown_error'),
                                            error_name=issue.get('error_name', issue.get('error_type', 'Unknown Error')),
                                            error_message=issue.get('description', ''),
                                            severity=issue.get('severity', 'medium'),
                                            category=issue.get('category', 'log_scan'),
                                            status='pending',
                                            error_metadata=issue.get('metadata', {}),
                                            discovered_at=datetime.utcnow()
                                        )
                                        db_session.add(error_record)
                                        total_errors_saved += 1

                                    await db_session.commit()
                                    logger.info(f"✅ Сохранено {len(issues)} ошибок для драйвера {driver_id[:8]} в базу данных")
                            except Exception as e:
                                logger.error(f"❌ Ошибка при сохранении результатов в БД для драйвера {driver_id[:8]}: {e}")
                    else:
                        failed_drivers += 1
                        error_msg = log_result.get('error', 'Unknown error')
                        driver_name_failed = log_result.get('driver_name', f'Driver {driver_id[:8]}')
                        logger.error(f"Failed to scan driver {driver_id[:8]}: {error_msg}")

                        # Сохраняем запись об ошибке сканирования в БД,
                        # чтобы она отображалась в Results даже при неудачном скане
                        try:
                            from app.database.models import Error
                            from app.database.session import get_db_session

                            async with get_db_session() as db_session:
                                scan_error = Error(
                                    driver_id=driver_id,
                                    driver_name=driver_name_failed,
                                    company_id=_company_id or 'unknown',
                                    company_name=_company_name or 'Unknown Company',
                                    error_key='scan_failed',
                                    error_name='Ошибка сканирования',
                                    error_message=f"Не удалось просканировать драйвера: {error_msg}",
                                    severity='high',
                                    category='diagnostic',
                                    status='failed',
                                    error_metadata={'scan_error': error_msg, 'scan_id': scan_id},
                                    discovered_at=datetime.utcnow()
                                )
                                db_session.add(scan_error)
                                await db_session.commit()
                                total_errors_saved += 1
                                logger.info(f"💾 Сохранена ошибка сканирования для драйвера {driver_id[:8]} в БД")
                        except Exception as save_err:
                            logger.error(f"❌ Не удалось сохранить ошибку сканирования: {save_err}")

                # Determine actual success based on results
                overall_success = successful_drivers > 0
                logger.info(f"Сканирование логов завершено: {successful_drivers} успешно, {failed_drivers} провалились, {total_errors_saved} ошибок сохранено")

                # ВАЖНО: complete_scan вызывается ТОЛЬКО здесь, после всей обработки
                # scan_drivers_parallel НЕ вызывает complete_scan чтобы избежать race condition
                if overall_success:
                    progress_tracker.complete_scan(scan_id, success=True, message=f"Завершено: {successful_drivers}/{len(log_results)} драйверов, {total_errors_saved} ошибок сохранено")
                else:
                    progress_tracker.complete_scan(scan_id, success=False, message=f"Провалено: все {failed_drivers} драйверов провалились")

            finally:
                await log_scanner.cleanup()

        except Exception as e:
            logger.exception(f"Сканирование логов провалилось: {e}")
            progress_tracker.complete_scan(scan_id, success=False, message=f"Ошибка: {str(e)}")

    # Start background task
    asyncio.create_task(run_log_scan_in_background())

    return {
        "status": "started",
        "scan_id": scan_id,
        "message": f"Log scan initiated for {len(driver_ids_to_scan)} drivers",
        "driver_count": len(driver_ids_to_scan),
        "company_id": request.company_id,
    }
