"""
OPIK Prompt Versioning API
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List, Dict, Any

from app.db.mongodb import get_async_db
from app.schemas.prompts import PromptTemplate, PromptVersion, PromptExperiment
from app.services.prompts import prompt_service

router = APIRouter(prefix="/prompts", tags=["prompts"])

# Prompt Templates

@router.post("/templates", response_model=Dict[str, str])
async def create_template(
    template: PromptTemplate,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Create a new prompt template
    """
    try:
        template_id = await prompt_service.create_template(db, template)
        return {"template_id": template_id}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating prompt template: {str(e)}"
        )

@router.get("/templates", response_model=List[PromptTemplate])
async def get_templates(
    tags: Optional[List[str]] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Get prompt templates, optionally filtered by tags
    """
    try:
        templates = await prompt_service.get_templates(db, tags, limit)
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving prompt templates: {str(e)}"
        )

@router.get("/templates/{template_id}", response_model=PromptTemplate)
async def get_template(
    template_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Get a specific prompt template
    """
    try:
        template = await prompt_service.get_template(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving prompt template: {str(e)}"
        )

@router.put("/templates/{template_id}", response_model=Dict[str, bool])
async def update_template(
    template: PromptTemplate,
    template_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Update a prompt template
    """
    try:
        # Ensure template ID matches path parameter
        if template.id != template_id:
            raise HTTPException(
                status_code=400,
                detail="Template ID in body does not match path parameter"
            )
        
        success = await prompt_service.update_template(db, template)
        if not success:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating prompt template: {str(e)}"
        )

@router.delete("/templates/{template_id}", response_model=Dict[str, bool])
async def delete_template(
    template_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Delete a prompt template and all its versions
    """
    try:
        success = await prompt_service.delete_template(db, template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting prompt template: {str(e)}"
        )

# Prompt Versions

@router.post("/versions", response_model=Dict[str, str])
async def create_version(
    version: PromptVersion,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Create a new prompt version
    """
    try:
        # Check if parent template exists
        template = await prompt_service.get_template(db, version.prompt_template_id)
        if not template:
            raise HTTPException(
                status_code=404, 
                detail=f"Parent template {version.prompt_template_id} not found"
            )
        
        version_id = await prompt_service.create_version(db, version)
        return {"version_id": version_id}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating prompt version: {str(e)}"
        )

@router.get("/templates/{template_id}/versions", response_model=List[PromptVersion])
async def get_versions_for_template(
    template_id: str = Path(...),
    active_only: bool = Query(False),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Get all versions for a template
    """
    try:
        # Check if template exists
        template = await prompt_service.get_template(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        versions = await prompt_service.get_versions_for_template(
            db, template_id, active_only
        )
        return versions
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving prompt versions: {str(e)}"
        )

@router.get("/versions/{version_id}", response_model=PromptVersion)
async def get_version(
    version_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Get a specific prompt version
    """
    try:
        version = await prompt_service.get_version(db, version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Prompt version not found")
        return version
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving prompt version: {str(e)}"
        )

@router.put("/versions/{version_id}", response_model=Dict[str, bool])
async def update_version(
    version: PromptVersion,
    version_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Update a prompt version
    """
    try:
        # Ensure version ID matches path parameter
        if version.id != version_id:
            raise HTTPException(
                status_code=400,
                detail="Version ID in body does not match path parameter"
            )
        
        success = await prompt_service.update_version(db, version)
        if not success:
            raise HTTPException(status_code=404, detail="Prompt version not found")
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating prompt version: {str(e)}"
        )

@router.put("/versions/{version_id}/metrics", response_model=Dict[str, bool])
async def update_version_metrics(
    metrics: Dict[str, Any],
    version_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Update performance metrics for a prompt version
    """
    try:
        # Check if version exists
        version = await prompt_service.get_version(db, version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Prompt version not found")
        
        success = await prompt_service.update_performance_metrics(
            db, version_id, metrics
        )
        
        return {"success": success}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating performance metrics: {str(e)}"
        )

# Prompt Experiments

@router.post("/experiments", response_model=Dict[str, str])
async def create_experiment(
    experiment: PromptExperiment,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Create a new prompt experiment
    """
    try:
        # Check if all prompt versions exist
        for version_id in experiment.prompt_versions:
            version = await prompt_service.get_version(db, version_id)
            if not version:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Prompt version {version_id} not found"
                )
        
        experiment_id = await prompt_service.create_experiment(db, experiment)
        return {"experiment_id": experiment_id}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating prompt experiment: {str(e)}"
        )

@router.get("/experiments/active", response_model=List[PromptExperiment])
async def get_active_experiments(
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Get all active prompt experiments
    """
    try:
        experiments = await prompt_service.get_active_experiments(db)
        return experiments
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving active experiments: {str(e)}"
        )

@router.get("/experiments/{experiment_id}", response_model=PromptExperiment)
async def get_experiment(
    experiment_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Get a specific prompt experiment
    """
    try:
        experiment = await prompt_service.get_experiment(db, experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Prompt experiment not found")
        return experiment
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving prompt experiment: {str(e)}"
        )

@router.put("/experiments/{experiment_id}/results", response_model=Dict[str, bool])
async def update_experiment_results(
    results: Dict[str, Any],
    experiment_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Update results for a prompt experiment
    """
    try:
        # Check if experiment exists
        experiment = await prompt_service.get_experiment(db, experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Prompt experiment not found")
        
        success = await prompt_service.update_experiment_results(
            db, experiment_id, results
        )
        
        return {"success": success}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating experiment results: {str(e)}"
        )

@router.put("/experiments/{experiment_id}/complete", response_model=Dict[str, bool])
async def complete_experiment(
    experiment_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Mark a prompt experiment as completed
    """
    try:
        # Check if experiment exists
        experiment = await prompt_service.get_experiment(db, experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Prompt experiment not found")
        
        success = await prompt_service.complete_experiment(db, experiment_id)
        
        return {"success": success}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error completing experiment: {str(e)}"
        ) 