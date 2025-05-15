"""
OPIK Prompt Versioning System Service
"""
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from app.schemas.prompts import PromptTemplate, PromptVersion, PromptExperiment

class PromptService:
    """Service for managing prompt templates, versions, and experiments"""
    
    def __init__(
        self, 
        template_collection: str = "prompt_templates",
        version_collection: str = "prompt_versions",
        experiment_collection: str = "prompt_experiments"
    ):
        """Initialize the prompt service"""
        self.template_collection = template_collection
        self.version_collection = version_collection
        self.experiment_collection = experiment_collection
    
    # Prompt Template Methods
    
    async def create_template(self, db: AsyncIOMotorDatabase, template: PromptTemplate) -> str:
        """
        Create a new prompt template
        
        Args:
            db: AsyncIOMotorDatabase instance
            template: The prompt template to create
            
        Returns:
            ID of the created template
        """
        collection = db[self.template_collection]
        result = await collection.insert_one(template.dict())
        return str(result.inserted_id)
    
    async def get_template(self, db: AsyncIOMotorDatabase, template_id: str) -> Optional[PromptTemplate]:
        """
        Get a prompt template by ID
        
        Args:
            db: AsyncIOMotorDatabase instance
            template_id: ID of the template to retrieve
            
        Returns:
            The prompt template or None if not found
        """
        collection = db[self.template_collection]
        result = await collection.find_one({"_id": template_id})
        
        if result:
            result["id"] = str(result.pop("_id"))
            return PromptTemplate(**result)
        return None
    
    async def get_templates(
        self, 
        db: AsyncIOMotorDatabase, 
        tags: Optional[List[str]] = None, 
        limit: int = 100
    ) -> List[PromptTemplate]:
        """
        Get prompt templates with optional tag filtering
        
        Args:
            db: AsyncIOMotorDatabase instance
            tags: Optional list of tags to filter by
            limit: Maximum number of templates to return
            
        Returns:
            List of prompt templates
        """
        collection = db[self.template_collection]
        query = {}
        
        if tags:
            query["tags"] = {"$in": tags}
        
        cursor = collection.find(query).limit(limit)
        templates = []
        
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            templates.append(PromptTemplate(**doc))
        
        return templates
    
    async def update_template(self, db: AsyncIOMotorDatabase, template: PromptTemplate) -> bool:
        """
        Update a prompt template
        
        Args:
            db: AsyncIOMotorDatabase instance
            template: The updated prompt template
            
        Returns:
            True if update was successful, False otherwise
        """
        collection = db[self.template_collection]
        template_dict = template.dict()
        template_id = template_dict.pop("id")
        
        result = await collection.update_one(
            {"_id": template_id},
            {"$set": template_dict}
        )
        return result.modified_count > 0
    
    async def delete_template(self, db: AsyncIOMotorDatabase, template_id: str) -> bool:
        """
        Delete a prompt template
        
        Args:
            db: AsyncIOMotorDatabase instance
            template_id: ID of the template to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        # First, delete all versions of this template
        version_collection = db[self.version_collection]
        await version_collection.delete_many({"prompt_template_id": template_id})
        
        # Then delete the template
        collection = db[self.template_collection]
        result = await collection.delete_one({"_id": template_id})
        return result.deleted_count > 0
    
    # Prompt Version Methods
    
    async def create_version(self, db: AsyncIOMotorDatabase, version: PromptVersion) -> str:
        """
        Create a new prompt version
        
        Args:
            db: AsyncIOMotorDatabase instance
            version: The prompt version to create
            
        Returns:
            ID of the created version
        """
        collection = db[self.version_collection]
        result = await collection.insert_one(version.dict())
        return str(result.inserted_id)
    
    async def get_version(self, db: AsyncIOMotorDatabase, version_id: str) -> Optional[PromptVersion]:
        """
        Get a prompt version by ID
        
        Args:
            db: AsyncIOMotorDatabase instance
            version_id: ID of the version to retrieve
            
        Returns:
            The prompt version or None if not found
        """
        collection = db[self.version_collection]
        result = await collection.find_one({"_id": version_id})
        
        if result:
            result["id"] = str(result.pop("_id"))
            return PromptVersion(**result)
        return None
    
    async def get_versions_for_template(
        self, 
        db: AsyncIOMotorDatabase, 
        template_id: str,
        active_only: bool = False
    ) -> List[PromptVersion]:
        """
        Get all versions for a template
        
        Args:
            db: AsyncIOMotorDatabase instance
            template_id: ID of the template to get versions for
            active_only: If True, return only active versions
            
        Returns:
            List of prompt versions
        """
        collection = db[self.version_collection]
        query = {"prompt_template_id": template_id}
        
        if active_only:
            query["is_active"] = True
        
        cursor = collection.find(query).sort("created_at", -1)
        versions = []
        
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            versions.append(PromptVersion(**doc))
        
        return versions
    
    async def update_version(self, db: AsyncIOMotorDatabase, version: PromptVersion) -> bool:
        """
        Update a prompt version
        
        Args:
            db: AsyncIOMotorDatabase instance
            version: The updated prompt version
            
        Returns:
            True if update was successful, False otherwise
        """
        collection = db[self.version_collection]
        version_dict = version.dict()
        version_id = version_dict.pop("id")
        
        result = await collection.update_one(
            {"_id": version_id},
            {"$set": version_dict}
        )
        return result.modified_count > 0
    
    async def update_performance_metrics(
        self, 
        db: AsyncIOMotorDatabase, 
        version_id: str, 
        metrics: Dict[str, Any]
    ) -> bool:
        """
        Update performance metrics for a prompt version
        
        Args:
            db: AsyncIOMotorDatabase instance
            version_id: ID of the version to update metrics for
            metrics: Performance metrics to update
            
        Returns:
            True if update was successful, False otherwise
        """
        collection = db[self.version_collection]
        result = await collection.update_one(
            {"_id": version_id},
            {
                "$set": {
                    "performance_metrics": metrics,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    # Prompt Experiment Methods
    
    async def create_experiment(self, db: AsyncIOMotorDatabase, experiment: PromptExperiment) -> str:
        """
        Create a new prompt experiment
        
        Args:
            db: AsyncIOMotorDatabase instance
            experiment: The prompt experiment to create
            
        Returns:
            ID of the created experiment
        """
        collection = db[self.experiment_collection]
        result = await collection.insert_one(experiment.dict())
        return str(result.inserted_id)
    
    async def get_experiment(self, db: AsyncIOMotorDatabase, experiment_id: str) -> Optional[PromptExperiment]:
        """
        Get a prompt experiment by ID
        
        Args:
            db: AsyncIOMotorDatabase instance
            experiment_id: ID of the experiment to retrieve
            
        Returns:
            The prompt experiment or None if not found
        """
        collection = db[self.experiment_collection]
        result = await collection.find_one({"_id": experiment_id})
        
        if result:
            result["id"] = str(result.pop("_id"))
            return PromptExperiment(**result)
        return None
    
    async def get_active_experiments(self, db: AsyncIOMotorDatabase) -> List[PromptExperiment]:
        """
        Get all active prompt experiments
        
        Args:
            db: AsyncIOMotorDatabase instance
            
        Returns:
            List of active prompt experiments
        """
        collection = db[self.experiment_collection]
        cursor = collection.find({"status": "active"})
        experiments = []
        
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            experiments.append(PromptExperiment(**doc))
        
        return experiments
    
    async def update_experiment(self, db: AsyncIOMotorDatabase, experiment: PromptExperiment) -> bool:
        """
        Update a prompt experiment
        
        Args:
            db: AsyncIOMotorDatabase instance
            experiment: The updated prompt experiment
            
        Returns:
            True if update was successful, False otherwise
        """
        collection = db[self.experiment_collection]
        experiment_dict = experiment.dict()
        experiment_id = experiment_dict.pop("id")
        
        result = await collection.update_one(
            {"_id": experiment_id},
            {"$set": experiment_dict}
        )
        return result.modified_count > 0
    
    async def update_experiment_results(
        self, 
        db: AsyncIOMotorDatabase, 
        experiment_id: str, 
        results: Dict[str, Any]
    ) -> bool:
        """
        Update results for a prompt experiment
        
        Args:
            db: AsyncIOMotorDatabase instance
            experiment_id: ID of the experiment to update results for
            results: Results to update
            
        Returns:
            True if update was successful, False otherwise
        """
        collection = db[self.experiment_collection]
        result = await collection.update_one(
            {"_id": experiment_id},
            {
                "$set": {
                    "results": results,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    async def complete_experiment(self, db: AsyncIOMotorDatabase, experiment_id: str) -> bool:
        """
        Mark a prompt experiment as completed
        
        Args:
            db: AsyncIOMotorDatabase instance
            experiment_id: ID of the experiment to complete
            
        Returns:
            True if update was successful, False otherwise
        """
        collection = db[self.experiment_collection]
        result = await collection.update_one(
            {"_id": experiment_id},
            {
                "$set": {
                    "status": "completed",
                    "end_date": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    async def get_default_for_character(
        self, 
        db: AsyncIOMotorDatabase, 
        character_id: str
    ) -> Optional[PromptVersion]:
        """
        Get the default prompt version for a character
        
        Args:
            db: AsyncIOMotorDatabase instance
            character_id: ID of the character
            
        Returns:
            Default prompt version for the character or None if not found
        """
        try:
            # First, check if there's a character-specific template
            collection = db[self.template_collection]
            template = await collection.find_one({"character_id": character_id, "is_default": True})
            
            if not template:
                # If no character-specific template, try to find a generic default
                template = await collection.find_one({"is_default": True, "character_id": {"$exists": False}})
            
            if not template:
                # No default template found
                return None
            
            # Get the latest active version of this template
            version_collection = db[self.version_collection]
            version = await version_collection.find_one(
                {"prompt_template_id": str(template["_id"]), "is_active": True},
                sort=[("created_at", -1)]
            )
            
            if version:
                version["id"] = str(version.pop("_id"))
                return PromptVersion(**version)
            
            return None
        except Exception as e:
            print(f"Error retrieving default prompt for character {character_id}: {str(e)}")
            return None

# Create a singleton instance
prompt_service = PromptService() 