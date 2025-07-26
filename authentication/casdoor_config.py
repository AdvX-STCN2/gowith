# Copyright 2024 The AdventureX-STCN2 Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf import settings
from casdoor import CasdoorSDK
from typing import Optional
import os


class CasdoorConfig:
    """Casdoor配置管理类"""
    
    _sdk_instance: Optional[CasdoorSDK] = None
    
    @classmethod
    def get_sdk(cls) -> CasdoorSDK:
        """获取CasdoorSDK实例（单例模式）"""
        if cls._sdk_instance is None:
            cls._sdk_instance = cls._create_sdk()
        return cls._sdk_instance
    
    @classmethod
    def _create_sdk(cls) -> CasdoorSDK:
        """创建CasdoorSDK实例"""
        # 读取证书文件
        certificate = cls._get_certificate()
        
        return CasdoorSDK(
            endpoint=settings.CASDOOR_ENDPOINT,
            client_id=settings.CASDOOR_CLIENT_ID,
            client_secret=settings.CASDOOR_CLIENT_SECRET,
            certificate=certificate,
            org_name=settings.CASDOOR_ORGANIZATION_NAME,
            application_name=settings.CASDOOR_APPLICATION_NAME,
            front_endpoint=getattr(settings, 'CASDOOR_FRONT_ENDPOINT', settings.CASDOOR_ENDPOINT)
        )
    
    @classmethod
    def _get_certificate(cls) -> str:
        """获取证书内容"""
        # 优先使用环境变量中的证书内容
        cert_content = getattr(settings, 'CASDOOR_CERTIFICATE_CONTENT', None)
        if cert_content:
            return cert_content
        
        # 从文件读取证书
        cert_file = getattr(settings, 'CASDOOR_CERTIFICATE_FILE', None)
        if cert_file and os.path.exists(cert_file):
            with open(cert_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        # 使用默认证书（仅用于开发环境）
        return cls._get_default_certificate()
    
    @classmethod
    def _get_default_certificate(cls) -> str:
        """获取默认证书（仅用于开发环境）"""
        return '''-----BEGIN CERTIFICATE-----
MIIE+TCCAuGgAwIBAgIDAeJAMA0GCSqGSIb3DQEBCwUAMDYxHTAbBgNVBAoTFENh
c2Rvb3IgT3JnYW5pemF0aW9uMRUwEwYDVQQDEwxDYXNkb29yIENlcnQwHhcNMjEx
MDE1MDgxMTUyWhcNNDExMDE1MDgxMTUyWjA2MR0wGwYDVQQKExRDYXNkb29yIE9y
Z2FuaXphdGlvbjEVMBMGA1UEAxMMQ2FzZG9vciBDZXJ0MIICIjANBgkqhkiG9w0B
AQEFAAOCAg8AMIICCgKCAgEAsInpb5E1/ym0f1RfSDSSE8IR7y+lw+RJjI74e5ej
rq4b8zMYk7HeHCyZr/hmNEwEVXnhXu1P0mBeQ5ypp/QGo8vgEmjAETNmzkI1NjOQ
CjCYwUrasO/f/MnI1C0j13vx6mV1kHZjSrKsMhYY1vaxTEP3+VB8Hjg3MHFWrb07
uvFMCJe5W8+0rKErZCKTR8+9VB3janeBz//zQePFVh79bFZate/hLirPK0Go9P1g
OvwIoC1A3sarHTP4Qm/LQRt0rHqZFybdySpyWAQvhNaDFE7mTstRSBb/wUjNCUBD
PTSLVjC04WllSf6Nkfx0Z7KvmbPstSj+btvcqsvRAGtvdsB9h62Kptjs1Yn7GAuo
I3qt/4zoKbiURYxkQJXIvwCQsEftUuk5ew5zuPSlDRLoLByQTLbx0JqLAFNfW3g/
pzSDjgd/60d6HTmvbZni4SmjdyFhXCDb1Kn7N+xTojnfaNkwep2REV+RMc0fx4Gu
hRsnLsmkmUDeyIZ9aBL9oj11YEQfM2JZEq+RVtUx+wB4y8K/tD1bcY+IfnG5rBpw
IDpS262boq4SRSvb3Z7bB0w4ZxvOfJ/1VLoRftjPbLIf0bhfr/AeZMHpIKOXvfz4
yE+hqzi68wdF0VR9xYc/RbSAf7323OsjYnjjEgInUtRohnRgCpjIk/Mt2Kt84Kb0
wn8CAwEAAaMQMA4wDAYDVR0TAQH/BAIwADANBgkqhkiG9w0BAQsFAAOCAgEAn2lf
DKkLX+F1vKRO/5gJ+Plr8P5NKuQkmwH97b8CS2gS1phDyNgIc4/LSdzuf4Awe6ve
C06lVdWSIis8UPUPdjmT2uMPSNjwLxG3QsrimMURNwFlLTfRem/heJe0Zgur9J1M
8haawdSdJjH2RgmFoDeE2r8NVRfhbR8KnCO1ddTJKuS1N0/irHz21W4jt4rxzCvl
2nR42Fybap3O/g2JXMhNNROwZmNjgpsF7XVENCSuFO1jTywLaqjuXCg54IL7XVLG
omKNNNcc8h1FCeKj/nnbGMhodnFWKDTsJcbNmcOPNHo6ixzqMy/Hqc+mWYv7maAG
Jtevs3qgMZ8F9Qzr3HpUc6R3ZYYWDY/xxPisuKftOPZgtH979XC4mdf0WPnOBLqL
2DJ1zaBmjiGJolvb7XNVKcUfDXYw85ZTZQ5b9clI4e+6bmyWqQItlwt+Ati/uFEV
XzCj70B4lALX6xau1kLEpV9O1GERizYRz5P9NJNA7KoO5AVMp9w0DQTkt+LbXnZE
HHnWKy8xHQKZF9sR7YBPGLs/Ac6tviv5Ua15OgJ/8dLRZ/veyFfGo2yZsI+hKVU5
nCCJHBcAyFnm1hdvdwEdH33jDBjNB6ciotJZrf/3VYaIWSalADosHAgMWfXuWP+h
8XKXmzlxuHbTMQYtZPDgspS5aK+S4Q9wb8RRAYo=
-----END CERTIFICATE-----'''
    
    @classmethod
    def get_redirect_uri(cls, request) -> str:
        """获取重定向URI"""
        # 使用前端地址构建回调URI，而不是后端地址
        frontend_endpoint = cls.get_frontend_endpoint()
        return f"{frontend_endpoint}/auth/callback"
    
    @classmethod
    def get_logout_redirect_uri(cls, request) -> str:
        """获取登出重定向URI"""
        return request.build_absolute_uri('/')
    
    @classmethod
    def get_frontend_endpoint(cls) -> str:
        """获取前端地址"""
        return getattr(settings, 'CASDOOR_FRONTEND_ENDPOINT', 'http://localhost:3000')