"""
Memory Module for character long-term memory
"""
# Use the real service with MongoDB Atlas
from app.memory.service import memory_service

__all__ = ['memory_service'] 