"""
Examination Standardization Service
Standardizes non-standard examination names using LLM + Knowledge Graph.
"""

from typing import List, Dict, Any, Optional
from fastapi import UploadFile
import pandas as pd
import io
import uuid
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app.services.examination_kg_service import examination_kg_service
from app.core.llm import llm_service
from app.db.base import SessionLocal
from app.db.models import StandardizationTask

logger = logging.getLogger(__name__)

class ExaminationStandardizationService:
    """
    Service for standardizing medical examination names.
    
    Workflow:
    1. Parse uploaded file (CSV/Excel)
    2. For each record, use LLM + KG to standardize
    3. Validate results against knowledge graph
    4. Return standardized results
    """
    
    
    def __init__(self):
        self.kg = examination_kg_service
        self._kg_initialized = False



    async def initialize_kg(self):
        """Ensure KG connection is active."""
        if not self._kg_initialized:
            # Add initialization logic if needed
            self._kg_initialized = True

    def create_task(self, filename: str, user: str = "system") -> str:
        """Create a new standardization task."""
        db = SessionLocal()
        try:
            task = StandardizationTask(
                id=str(uuid.uuid4()),
                filename=filename,
                user=user,
                status="processing",
                results=json.dumps([])
            )
            db.add(task)
            db.commit()
            return task.id
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task status and info."""
        db = SessionLocal()
        try:
            task = db.query(StandardizationTask).filter(StandardizationTask.id == task_id).first()
            if not task:
                return None
            
            # Convert to dict
            return {
                "id": task.id,
                "filename": task.filename,
                "status": task.status,
                "user": task.user,
                "total_records": task.total_records,
                "processed_records": task.processed_records,
                "success_count": task.success_count,
                "failed_count": task.failed_count,
                "error_message": task.error_message,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            }
        finally:
            db.close()

    def get_task_results(self, task_id: str) -> List[Dict]:
        """Get processed results for a task."""
        db = SessionLocal()
        try:
            task = db.query(StandardizationTask).filter(StandardizationTask.id == task_id).first()
            if not task or not task.results:
                return []
            return json.loads(task.results)
        finally:
            db.close()

    def update_task_results(self, task_id: str, results: List[Dict]) -> bool:
        """Update processed results for a task (Manual Correction)."""
        db = SessionLocal()
        try:
            task = db.query(StandardizationTask).filter(StandardizationTask.id == task_id).first()
            if not task:
                return False
            
            # Verify structure (basic check)
            if not isinstance(results, list):
                return False
                
            task.results = json.dumps(results, ensure_ascii=False)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update task results: {e}")
            db.rollback()
            return False
        finally:
            db.close()
            
    def get_all_tasks(self, limit: int = 50) -> List[Dict]:
        """Get historical tasks."""
        db = SessionLocal()
        try:
            tasks = db.query(StandardizationTask)\
                .order_by(StandardizationTask.created_at.desc())\
                .limit(limit)\
                .all()
                
            return [{
                "id": t.id,
                "filename": t.filename,
                "status": t.status,
                "user": t.user,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "total_records": t.total_records,
                "success_count": t.success_count,
                "failed_count": t.failed_count
            } for t in tasks]
        finally:
            db.close()

    async def process_file(self, task_id: str, content: bytes, filename: str):
        """Process uploaded file in background."""
        db = SessionLocal()
        try:
            # Update status
            task = db.query(StandardizationTask).filter(StandardizationTask.id == task_id).first()
            if not task:
                return
            
            # Parse file
            if filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(content))
            else:
                df = pd.read_excel(io.BytesIO(content))
                
            records = df.to_dict('records')
            
            task.total_records = len(records)
            db.commit()
            
            logger.info(f"Parsed {len(records)} records from {filename}")
            
            results_list = []
            
            # Process in batches
            BATCH_SIZE = 10
            
            for i in range(0, len(records), BATCH_SIZE):
                batch_records = records[i:i + BATCH_SIZE]
                tasks = []
                batch_indices = []
                
                # Prepare tasks
                for batch_idx, record in enumerate(batch_records):
                    global_idx = i + batch_idx
                    exam_name = record.get("检查项目名", record.get("exam_name", ""))
                    modality = record.get("检查标准模态", record.get("modality", ""))
                    
                    if not exam_name:
                        logger.warning(f"Record {global_idx} missing exam name, skipping")
                        task.failed_count += 1
                        task.processed_records += 1
                        continue
                        
                    tasks.append(self._standardize_single(exam_name, modality))
                    batch_indices.append(global_idx) # Keep track of which record this is
                
                if not tasks:
                    continue
                    
                # Execute batch concurrently
                try:
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for res_idx, result in enumerate(batch_results):
                        original_record = batch_records[batch_indices[res_idx] - i] # Get original record
                        exam_name = original_record.get("检查项目名", original_record.get("exam_name", ""))
                        modality = original_record.get("检查标准模态", original_record.get("modality", ""))
                        
                        if isinstance(result, Exception):
                            logger.error(f"Error processing record {batch_indices[res_idx]}: {result}")
                            task.failed_count += 1
                            result_data = None
                            status = "failed"
                        elif result is None:
                            task.failed_count += 1
                            result_data = None
                            status = "failed"
                        else:
                            # Result is a dict with {result, status}
                            result_data = result.get("result")
                            status = result.get("status", "success")
                            
                            if status == "success":
                                task.success_count += 1
                            elif status == "review_required":
                                # Treat as success for counting? Or separate? 
                                # For now count as success (processed) but status differs
                                task.success_count += 1
                            else:
                                task.failed_count += 1
                            
                        results_list.append({
                            "original_name": exam_name,
                            "modality": modality,
                            "standardized": result_data,
                            "status": status
                        })
                        
                        task.processed_records += 1
                        
                    # Periodic commit after each batch
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Batch processing error at index {i}: {e}")
                    # If batch fails catastrophically, we might lose some progress updates, 
                    # but we try to continue or just log.
                    # Ideally we should shouldn't hit this with return_exceptions=True
            
            # Final update
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.results = json.dumps(results_list, ensure_ascii=False)
            db.commit()
            
            logger.info(f"Task {task_id} completed: {task.success_count} success, {task.failed_count} failed")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            # Re-fetch task to ensure session is valid
            db.rollback() 
            task = db.query(StandardizationTask).filter(StandardizationTask.id == task_id).first()
            if task:
                task.status = "failed"
                task.error_message = str(e)
                db.commit()
        finally:
            db.close()

    async def _standardize_single(self, exam_name: str, modality: str) -> Optional[Dict]:
        """
        Standardize a single examination name.
        Returns dict: { "result": [...], "status": "success" | "review_required" }
        """
        try:
            # --- Stage 1: Identify Level 1 Body Part(s) ---
            level1_parts = await self.kg.get_all_level1_parts()
            prompt1 = self._build_level1_prompt(exam_name, level1_parts)
            response1 = await self._call_llm(prompt1)
            
            # Parse multiple level 1 parts
            identified_level1_list = self._parse_level1_response(response1, level1_parts)
            
            if not identified_level1_list:
                logger.warning(f"Stage 1 failed: Could not identify Level 1 part for '{exam_name}'")
                return None
                
            logger.info(f"Stage 1 identified: {identified_level1_list} for '{exam_name}'")

            # --- Stage 2: Detailed Parsing ---
            # Fetch specific Level 2 parts for ALL identified Level 1s
            all_level2_candidates = []
            for l1 in identified_level1_list:
                l2_parts = await self.kg.get_level2_parts(l1)
                all_level2_candidates.extend(l2_parts)
            
            # Remove duplicates just in case
            all_level2_candidates = list(set(all_level2_candidates))
            
            prompt2 = await self._build_detailed_prompt(
                exam_name, 
                modality, 
                identified_level1_list, 
                all_level2_candidates
            )
            
            response2 = await self._call_llm(prompt2)
            parsed_result = self._parse_llm_response(response2)
            
            # Validate against KG
            is_valid = await self._validate_against_kg(parsed_result)
            
            status = "success" if is_valid else "review_required"
            
            return {
                "result": parsed_result,
                "status": status
            }
            
        except Exception as e:
            logger.error(f"Standardization failed for {exam_name}: {e}")
            return None
    
    def _build_level1_prompt(self, exam_name: str, level1_candidates: List[str]) -> str:
        """Build prompt for Stage 1: Level 1 Identification."""
        return f"""你是一个医学专家。请判断以下检查项目属于哪些"一级检查部位"。

候选一级部位: {', '.join(level1_candidates)}

输入: {exam_name}
规则:
1. 输出所有匹配的一级部位名称,用逗号分隔。
2. 如果包含多个部位(如"头胸腹CT"),请输出"头颈部, 胸部, 腹部"。
3. 如果不确定,输出"Unknown"。
"""

    def _parse_level1_response(self, response: str, candidates: List[str]) -> List[str]:
        """Parse Stage 1 response (returns list of Level 1s)."""
        cleaned = response.strip().replace('"', '').replace("'", "")
        found = []
        for candidate in candidates:
            if candidate in cleaned:
                found.append(candidate)
        return found

    async def _build_detailed_prompt(self, exam_name: str, modality: str, level1_list: List[str], level2_candidates: List[str]) -> str:
        """Build prompt for Stage 2: Detailed Parsing."""
        
        # Get methods relevant to input modality
        if modality:
            methods = await self.kg.get_methods_by_modality(modality)
        else:
            methods = await self.kg.get_all_methods()
            methods = methods[:20] 
        
        level1_str = ", ".join(level1_list)
        
        prompt = f"""你是一个医学影像检查项目标准化专家。请将非标准的检查项目名称解析为标准三元组格式。

# 已知信息
涉及的一级部位: {level1_str}

# 候选二级部位 (限制在此范围内)
{', '.join(level2_candidates)}

# 候选检查方法
{', '.join(methods)}...

# 示例

输入: 单手指正侧位片, 模态: DR
输出: [["上肢", "手指", "正位"], ["上肢", "手指", "侧位"]]

输入: 双膝关节正位, 模态: DR  
输出: [["下肢", "膝关节", "正位"]]

输入: 腰椎正侧位, 模态: DR
输出: [["脊柱", "腰椎", "正位"], ["脊柱", "腰椎", "侧位"]]

输入: 胸部CT平扫, 模态: CT
输出: [["胸部", "胸廓", "轴位"]]

输入: 左手正位, 模态: DR
输出: [["上肢", "手掌", "正位"]]

# 规则
1. 如果名称中包含"正侧位"、"正斜位"等组合方法,拆分为多个三元组
2. "双"、"单"、"左"、"右"等修饰词不影响标准化结果
3. 二级部位必须属于对应的一级部位
4. 如果无法确定具体部位,选择最可能的部位
5. 只输出JSON数组,不要其他解释

输入: {exam_name}, 模态: {modality}
输出:
"""
        return prompt

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API."""
        client = llm_service.get_client()
        if not client:
            raise ValueError("LLM client not initialized. Please set OPENAI_API_KEY.")

        try:
            response = await client.chat.completions.create(
                model=llm_service.get_model_name(),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise
    
    def _parse_llm_response(self, response: str) -> List[List[str]]:
        """Parse LLM JSON response."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            response = response.strip()
            if response.startswith("```"):
                # Remove markdown code block markers
                lines = response.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                response = "\n".join(lines)
            
            # Parse JSON
            parsed = json.loads(response)
            
            # Basic validation
            if not isinstance(parsed, list):
                return []
                
            valid_triples = []
            for item in parsed:
                if isinstance(item, list) and len(item) == 3:
                    valid_triples.append(item)
            
            return valid_triples
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return []

    async def _validate_against_kg(self, triples: List[List[str]]) -> bool:
        """Validate triples against KG. Returns True if ALL triples are valid."""
        if not triples:
            return False
            
        all_valid = True
        for triple in triples:
            if len(triple) != 3:
                all_valid = False
                continue
                
            level1, level2, method = triple
            
            # Use KG service to validate path
            exists = await self.kg.validate_standardization_path(level1, level2, method)
            
            if not exists:
                logger.warning(f"Validation failed for path: {triple}")
                all_valid = False
                
        return all_valid


examination_service = ExaminationStandardizationService()
