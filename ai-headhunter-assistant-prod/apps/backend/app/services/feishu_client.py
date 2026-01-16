"""
飞书 API 客户端
"""

import base64
import logging
from typing import Optional, Dict, Any, List
import lark_oapi as lark
from lark_oapi.api.auth.v3 import *
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.drive.v1 import *

from ..config import get_feishu_config

logger = logging.getLogger(__name__)


class FeishuClient:
    """飞书 API 客户端"""
    
    def __init__(self):
        """初始化飞书客户端"""
        self.config = get_feishu_config()
        self.client = None
        self._access_token = None
        
        if self.config["enabled"]:
            self._initialize_client()
        else:
            logger.warning("飞书集成未启用，请配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
    
    def _initialize_client(self):
        """初始化飞书 SDK 客户端"""
        try:
            self.client = lark.Client.builder() \
                .app_id(self.config["app_id"]) \
                .app_secret(self.config["app_secret"]) \
                .log_level(lark.LogLevel.DEBUG) \
                .build()
            
            logger.info("飞书客户端初始化成功")
        except Exception as e:
            logger.error(f"飞书客户端初始化失败: {e}")
            raise
    
    async def get_tenant_access_token(self) -> Optional[str]:
        """获取 tenant_access_token
        
        Returns:
            str: Access Token，失败返回 None
        """
        if not self.config["enabled"] or not self.client:
            logger.warning("飞书未启用或客户端未初始化")
            return None
        
        try:
            # 创建请求对象
            request = InternalTenantAccessTokenRequest.builder() \
                .request_body(InternalTenantAccessTokenRequestBody.builder()
                    .app_id(self.config["app_id"])
                    .app_secret(self.config["app_secret"])
                    .build()) \
                .build()
            
            # 发起请求
            response = self.client.auth.v3.tenant_access_token.internal(request)
            
            # 处理响应
            if not response.success():
                logger.error(
                    f"获取 token 失败: code={response.code}, msg={response.msg}, "
                    f"log_id={response.get_log_id()}"
                )
                return None
            
            # 兼容不同版本的 SDK
            token = None
            if hasattr(response, 'data') and response.data:
                if hasattr(response.data, 'tenant_access_token'):
                    token = response.data.tenant_access_token
            elif hasattr(response, 'tenant_access_token'):
                token = response.tenant_access_token
            
            # 尝试直接从 JSON 响应中获取
            if not token and hasattr(response, 'raw') and hasattr(response.raw, 'content'):
                import json
                try:
                    json_data = json.loads(response.raw.content)
                    token = json_data.get('tenant_access_token')
                except:
                    pass
            
            if not token:
                logger.error(f"无法从响应中获取 token，响应对象: {response}")
                return None
                
            self._access_token = token
            logger.info("获取 tenant_access_token 成功")
            return token
            
        except Exception as e:
            logger.error(f"获取 tenant_access_token 异常: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            dict: 健康检查结果
        """
        if not self.config["enabled"]:
            return {
                "status": "disabled",
                "message": "飞书集成未启用"
            }
        
        # 尝试获取 Token
        token = await self.get_tenant_access_token()
        
        if token:
            return {
                "status": "healthy",
                "message": "飞书 API 连接正常",
                "app_id": self.config["app_id"][:10] + "...",  # 脱敏
                "token_obtained": True
            }
        else:
            return {
                "status": "error",
                "message": "飞书 API 连接失败，无法获取 Token"
            }
    
    def is_enabled(self) -> bool:
        """检查飞书集成是否启用"""
        return self.config["enabled"]
    
    async def upload_image(self, image_base64: str, filename: str) -> Optional[str]:
        """上传图片到飞书云盘
        
        Args:
            image_base64: Base64 编码的图片（可能包含 data:image/png;base64, 前缀）
            filename: 文件名
            
        Returns:
            str: 文件 Token，失败返回 None
        """
        if not self.config["enabled"] or not self.client:
            logger.warning("飞书未启用或客户端未初始化")
            return None
        
        try:
            # 清理 Base64 前缀
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            
            # 解码 Base64
            image_data = base64.b64decode(image_base64)
            
            logger.info(f"开始上传图片: {filename}, 大小: {len(image_data)} bytes")
            
            # 将字节数据包装成文件对象
            from io import BytesIO
            file_obj = BytesIO(image_data)
            file_obj.name = filename  # 设置文件名属性
            
            # 获取 app_token（多维表格的 parent_node）
            app_token = self.config["app_token"]
            
            # 创建上传请求（使用文件对象）
            request = UploadAllMediaRequest.builder() \
                .request_body(UploadAllMediaRequestBody.builder()
                    .file_name(filename)
                    .parent_type("bitable_image")
                    .parent_node(app_token)  # 使用 app_token 作为 parent_node
                    .size(len(image_data))
                    .file(file_obj)
                    .build()) \
                .build()
            
            # 发起请求
            response = self.client.drive.v1.media.upload_all(request)
            
            # 处理响应
            if not response.success():
                logger.error(
                    f"上传图片失败: code={response.code}, msg={response.msg}, "
                    f"log_id={response.get_log_id()}"
                )
                return None
            
            file_token = response.data.file_token
            logger.info(f"图片上传成功: file_token={file_token}")
            return file_token
            
        except Exception as e:
            logger.error(f"上传图片异常: {e}")
            return None
    
    async def add_record(
        self, 
        candidate_data: Dict[str, Any],
        screenshot_base64: Optional[str] = None
    ) -> Optional[str]:
        """添加候选人记录到多维表格
        
        Args:
            candidate_data: 候选人数据
            screenshot_base64: 简历截图 Base64（可选）
            
        Returns:
            str: 记录 ID，失败返回 None
        """
        if not self.config["enabled"] or not self.client:
            logger.warning("飞书未启用或客户端未初始化")
            return None
        
        app_token = self.config["app_token"]
        table_id = self.config["table_id"]
        
        if not app_token or not table_id:
            logger.error("未配置 FEISHU_APP_TOKEN 或 FEISHU_TABLE_ID")
            return None
        
        try:
            # 1. 如果有截图，先上传
            screenshot_token = None
            if screenshot_base64:
                logger.info(f"📸 准备上传截图，数据长度: {len(screenshot_base64)} 字符")
                filename = f"{candidate_data.get('name', 'candidate')}_{candidate_data.get('candidate_id', 'unknown')}.png"
                screenshot_token = await self.upload_image(screenshot_base64, filename)
                
                if screenshot_token:
                    logger.info(f"✅ 截图上传成功: {screenshot_token}")
                else:
                    logger.warning("❌ 截图上传失败，但继续添加记录")
            else:
                logger.info("ℹ️ 未提供截图数据，跳过上传")
            
            # 2. 构建记录字段
            from datetime import datetime
            
            fields = {
                "文本": candidate_data.get("candidate_id", ""),  # 使用「文本」字段存储候选人ID
                "姓名": candidate_data.get("name", ""),
                "年龄": candidate_data.get("age"),
                "工作年限": candidate_data.get("work_years"),
                "学历": candidate_data.get("education", ""),
                "当前公司": candidate_data.get("current_company", ""),
                "当前职位": candidate_data.get("current_position", ""),
                "期望薪资": candidate_data.get("salary", ""),
                "匹配度": candidate_data.get("match_score", 0) / 100,  # 转换为小数（飞书百分比字段）
                "推荐等级": candidate_data.get("recommend_level", ""),
                "核心优势": candidate_data.get("advantages", ""),
                "潜在风险": candidate_data.get("risks", ""),
                "活跃度": candidate_data.get("active_status", ""),
                "到岗状态": candidate_data.get("employment_status", ""),
                "采集时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            # 处理链接类型字段（数据来源）
            source_url = candidate_data.get("source_url", "")
            if source_url:
                fields["数据来源"] = {
                    "link": source_url,
                    "text": "Boss直聘"
                }
            
            # 3. 添加截图附件（如果有）
            if screenshot_token:
                fields["简历截图"] = [{
                    "file_token": screenshot_token,
                    "type": "image",
                    "name": filename
                }]
            
            # 4. 创建记录
            request = CreateAppTableRecordRequest.builder() \
                .app_token(app_token) \
                .table_id(table_id) \
                .request_body(AppTableRecord.builder()
                    .fields(fields)
                    .build()) \
                .build()
            
            # 5. 发起请求
            response = self.client.bitable.v1.app_table_record.create(request)
            
            # 6. 处理响应
            if not response.success():
                logger.error(
                    f"添加记录失败: code={response.code}, msg={response.msg}, "
                    f"log_id={response.get_log_id()}"
                )
                return None
            
            record_id = response.data.record.record_id
            logger.info(f"记录添加成功: record_id={record_id}")
            return record_id
            
        except Exception as e:
            logger.error(f"添加记录异常: {e}")
            return None
    
    async def check_duplicate(self, name: str, company: str) -> Optional[str]:
        """检查是否存在重复记录
        
        Args:
            name: 候选人姓名
            company: 当前公司
            
        Returns:
            str: 如果存在重复记录，返回记录 ID，否则返回 None
        """
        if not self.config["enabled"] or not self.client:
            return None
        
        app_token = self.config["app_token"]
        table_id = self.config["table_id"]
        
        if not app_token or not table_id:
            return None
        
        try:
            # 构建查询条件
            filter_condition = f'AND(CurrentValue.[姓名]="{name}",CurrentValue.[当前公司]="{company}")'
            
            # 创建查询请求
            request = ListAppTableRecordRequest.builder() \
                .app_token(app_token) \
                .table_id(table_id) \
                .filter(filter_condition) \
                .page_size(1) \
                .build()
            
            # 发起请求
            response = self.client.bitable.v1.app_table_record.list(request)
            
            # 处理响应
            if not response.success():
                logger.error(f"查询记录失败: {response.msg}")
                return None
            
            # 检查是否有结果
            if response.data.items and len(response.data.items) > 0:
                record_id = response.data.items[0].record_id
                logger.info(f"发现重复记录: {name} - {company}, record_id={record_id}")
                return record_id
            
            return None
            
        except Exception as e:
            logger.error(f"检查重复记录异常: {e}")
            return None


# 全局飞书客户端实例
feishu_client = FeishuClient()

