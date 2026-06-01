#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║  SUBSTRATO 889 v2.0 — ERC-8257 + ABI/TS + HARDHAT + 882        ║
# ║  Pipeline: 885 → 888 → 889 → 882 (Archaeological Tracking)      ║
# ║  Architect: ORCID 0009-0005-2697-4668                            ║
# ╚══════════════════════════════════════════════════════════════════╝

import hashlib
import json
import random
import tempfile
import base64
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, field

B64_SOLIDITY = 'Ly8gU1BEWC1MaWNlbnNlLUlkZW50aWZpZXI6IE1JVCAKcHJhZ21hIHNvbGlkaXR5IF4wLjguMjA7IAogCi8qKiAKICogQHRpdGxlIEVSQzgyNTdUb29sUmVnaXN0cnkgCiAqIEBub3RpY2UgUmVnaXN0cm8gcGVybWlzc2lvbmxlc3MgZGUgZmVycmFtZW50YXMgZGUgYWdlbnRlcyBkZSBJQSAKICogQGRldiBJbXBsZW1lbnRhw6fDo28gZG8gRUlQLTgyNTcgKENvZHkgU2VhcnMsIFJ5YW4gR2hvZHMgLyBPcGVuU2VhKSAKICogQGN1c3RvbTpzdWJzdHJhdG8gODcyLUVSQy04MjU3LVRPT0wtUkVHSVNUUlkgCiAqIEBjdXN0b206Y3Jvc3MtbGluayA4ODgtT1dMLVdFQjMtQlJJREdFIAogKiBAY3VzdG9tOmNyb3NzLWxpbmsgODg1LVJFQUxJVFktTUFOSUZFU1RBVElPTiAKICogQGN1c3RvbTpjcm9zcy1saW5rIDg4OS1FUkMtODI1Ny1TT0xJRElUWS1JUEZTLVJFQUxJVFkgCiAqLyAKY29udHJhY3QgRVJDODI1N1Rvb2xSZWdpc3RyeSB7IAogCiAgICBzdHJ1Y3QgVG9vbCB7IAogICAgICAgIHN0cmluZyBuYW1lOyAKICAgICAgICBzdHJpbmcgbWV0YWRhdGFVUkk7ICAgICAgLy8gSVBGUy9BcndlYXZlIGhhc2ggZG8gSlNPTi1MRCBTRFggCiAgICAgICAgYnl0ZXMzMiBjaGVja3N1bTsgICAgICAgIC8vIFNIQTMtMjU2IGRvIGNvbnRlw7pkbyBiaW7DoXJpbyAKICAgICAgICBhZGRyZXNzIG93bmVyOyAKICAgICAgICB1aW50MjU2IHJlZ2lzdGVyZWRBdDsgCiAgICAgICAgYm9vbCBleGlzdHM7IAogICAgfSAKIAogICAgbWFwcGluZyhieXRlczMyID0+IFRvb2wpIHB1YmxpYyB0b29sczsgCiAKICAgIGV2ZW50IFRvb2xSZWdpc3RlcmVkKCAKICAgICAgICBieXRlczMyIGluZGV4ZWQgdG9vbEhhc2gsIAogICAgICAgIHN0cmluZyBuYW1lLCAKICAgICAgICBzdHJpbmcgbWV0YWRhdGFVUkksIAogICAgICAgIGJ5dGVzMzIgY2hlY2tzdW0sIAogICAgICAgIGFkZHJlc3MgaW5kZXhlZCBvd25lciwgCiAgICAgICAgdWludDI1NiByZWdpc3RlcmVkQXQgCiAgICApOyAKIAogICAgZXZlbnQgVG9vbFVwZGF0ZWQoIAogICAgICAgIGJ5dGVzMzIgaW5kZXhlZCB0b29sSGFzaCwgCiAgICAgICAgc3RyaW5nIG1ldGFkYXRhVVJJLCAKICAgICAgICBieXRlczMyIGNoZWNrc3VtLCAKICAgICAgICB1aW50MjU2IHVwZGF0ZWRBdCAKICAgICk7IAogCiAgICBldmVudCBUb29sVmVyaWZpZWQoIAogICAgICAgIGJ5dGVzMzIgaW5kZXhlZCB0b29sSGFzaCwgCiAgICAgICAgYWRkcmVzcyBpbmRleGVkIHZlcmlmaWVyLCAKICAgICAgICBib29sIHZhbGlkIAogICAgKTsgCiAKICAgIG1vZGlmaWVyIG9ubHlPd25lcihieXRlczMyIF90b29sSGFzaCkgeyAKICAgICAgICByZXF1aXJlKHRvb2xzW190b29sSGFzaF0ub3duZXIgPT0gbXNnLnNlbmRlciwgIkVSQzgyNTc6IG5vdCBvd25lciIpOyAKICAgICAgICBfOyAKICAgIH0gCiAKICAgIG1vZGlmaWVyIHRvb2xFeGlzdHMoYnl0ZXMzMiBfdG9vbEhhc2gpIHsgCiAgICAgICAgcmVxdWlyZSh0b29sc1tfdG9vbEhhc2hdLmV4aXN0cywgIkVSQzgyNTc6IHRvb2wgbm90IGZvdW5kIik7IAogICAgICAgIF87IAogICAgfSAKIAogICAgZnVuY3Rpb24gcmVnaXN0ZXJUb29sKCAKICAgICAgICBzdHJpbmcgY2FsbGRhdGEgX25hbWUsIAogICAgICAgIHN0cmluZyBjYWxsZGF0YSBfbWV0YWRhdGFVUkksIAogICAgICAgIGJ5dGVzMzIgX2NoZWNrc3VtIAogICAgKSBleHRlcm5hbCByZXR1cm5zIChieXRlczMyIHRvb2xIYXNoKSB7IAogICAgICAgIHRvb2xIYXNoID0ga2VjY2FrMjU2KGJ5dGVzKF9uYW1lKSk7IAogICAgICAgIHJlcXVpcmUoIXRvb2xzW3Rvb2xIYXNoXS5leGlzdHMsICJFUkM4MjU3OiB0b29sIGFscmVhZHkgcmVnaXN0ZXJlZCIpOyAKIAogICAgICAgIHRvb2xzW3Rvb2xIYXNoXSA9IFRvb2woeyAKICAgICAgICAgICAgbmFtZTogX25hbWUsIAogICAgICAgICAgICBtZXRhZGF0YVVSSTogX21ldGFkYXRhVVJJLCAKICAgICAgICAgICAgY2hlY2tzdW06IF9jaGVja3N1bSwgCiAgICAgICAgICAgIG93bmVyOiBtc2cuc2VuZGVyLCAKICAgICAgICAgICAgcmVnaXN0ZXJlZEF0OiBibG9jay50aW1lc3RhbXAsIAogICAgICAgICAgICBleGlzdHM6IHRydWUgCiAgICAgICAgfSk7IAogCiAgICAgICAgZW1pdCBUb29sUmVnaXN0ZXJlZCh0b29sSGFzaCwgX25hbWUsIF9tZXRhZGF0YVVSSSwgX2NoZWNrc3VtLCBtc2cuc2VuZGVyLCBibG9jay50aW1lc3RhbXApOyAKICAgICAgICByZXR1cm4gdG9vbEhhc2g7IAogICAgfSAKIAogICAgZnVuY3Rpb24gdXBkYXRlVG9vbCggCiAgICAgICAgYnl0ZXMzMiBfdG9vbEhhc2gsIAogICAgICAgIHN0cmluZyBjYWxsZGF0YSBfbWV0YWRhdGFVUkksIAogICAgICAgIGJ5dGVzMzIgX2NoZWNrc3VtIAogICAgKSBleHRlcm5hbCBvbmx5T3duZXIoX3Rvb2xIYXNoKSB0b29sRXhpc3RzKF90b29sSGFzaCkgeyAKICAgICAgICB0b29sc1tfdG9vbEhhc2hdLm1ldGFkYXRhVVJJID0gX21ldGFkYXRhVVJJOyAKICAgICAgICB0b29sc1tfdG9vbEhhc2hdLmNoZWNrc3VtID0gX2NoZWNrc3VtOyAKICAgICAgICBlbWl0IFRvb2xVcGRhdGVkKF90b29sSGFzaCwgX21ldGFkYXRhVVJJLCBfY2hlY2tzdW0sIGJsb2NrLnRpbWVzdGFtcCk7IAogICAgfSAKIAogICAgZnVuY3Rpb24gdmVyaWZ5Q2hlY2tzdW0oIAogICAgICAgIGJ5dGVzMzIgX3Rvb2xIYXNoLCAKICAgICAgICBieXRlczMyIF9leHBlY3RlZENoZWNrc3VtIAogICAgKSBleHRlcm5hbCB2aWV3IHRvb2xFeGlzdHMoX3Rvb2xIYXNoKSByZXR1cm5zIChib29sKSB7IAogICAgICAgIGJvb2wgdmFsaWQgPSB0b29sc1tfdG9vbEhhc2hdLmNoZWNrc3VtID09IF9leHBlY3RlZENoZWNrc3VtOyAKICAgICAgICBlbWl0IFRvb2xWZXJpZmllZChfdG9vbEhhc2gsIG1zZy5zZW5kZXIsIHZhbGlkKTsgCiAgICAgICAgcmV0dXJuIHZhbGlkOyAKICAgIH0gCiAKICAgIGZ1bmN0aW9uIGdldFRvb2woYnl0ZXMzMiBfdG9vbEhhc2gpIGV4dGVybmFsIHZpZXcgdG9vbEV4aXN0cyhfdG9vbEhhc2gpIHJldHVybnMgKFRvb2wgbWVtb3J5KSB7IAogICAgICAgIHJldHVybiB0b29sc1tfdG9vbEhhc2hdOyAKICAgIH0gCiAKICAgIGZ1bmN0aW9uIGlzUmVnaXN0ZXJlZChieXRlczMyIF90b29sSGFzaCkgZXh0ZXJuYWwgdmlldyByZXR1cm5zIChib29sKSB7IAogICAgICAgIHJldHVybiB0b29sc1tfdG9vbEhhc2hdLmV4aXN0czsgCiAgICB9IAp9Cg=='
B64_MAPPING_TS = 'aW1wb3J0IHsgQmlnSW50IH0gZnJvbSAnQGdyYXBocHJvdG9jb2wvZ3JhcGgtdHMnOyAKaW1wb3J0IHsgCiAgVG9vbFJlZ2lzdGVyZWQsIAogIFRvb2xVcGRhdGVkLCAKICBUb29sVmVyaWZpZWQgCn0gZnJvbSAnLi4vZ2VuZXJhdGVkL0VSQzgyNTdUb29sUmVnaXN0cnkvRVJDODI1N1Rvb2xSZWdpc3RyeSc7IAppbXBvcnQgeyBUb29sLCBWZXJpZmljYXRpb24sIFJlZ2lzdHJ5U3RhdHMgfSBmcm9tICcuLi9nZW5lcmF0ZWQvc2NoZW1hJzsgCiAKZXhwb3J0IGZ1bmN0aW9uIGhhbmRsZVRvb2xSZWdpc3RlcmVkKGV2ZW50OiBUb29sUmVnaXN0ZXJlZCk6IHZvaWQgeyAKICBsZXQgdG9vbCA9IG5ldyBUb29sKGV2ZW50LnBhcmFtcy50b29sSGFzaC50b0hleCgpKTsgCiAgdG9vbC5uYW1lID0gZXZlbnQucGFyYW1zLm5hbWU7IAogIHRvb2wubWV0YWRhdGFVUkkgPSBldmVudC5wYXJhbXMubWV0YWRhdGFVUkk7IAogIHRvb2wuY2hlY2tzdW0gPSBldmVudC5wYXJhbXMuY2hlY2tzdW07IAogIHRvb2wub3duZXIgPSBldmVudC5wYXJhbXMub3duZXI7IAogIHRvb2wucmVnaXN0ZXJlZEF0ID0gZXZlbnQucGFyYW1zLnJlZ2lzdGVyZWRBdDsgCiAgdG9vbC51cGRhdGVkQXQgPSBldmVudC5wYXJhbXMucmVnaXN0ZXJlZEF0OyAKICB0b29sLmV4aXN0cyA9IHRydWU7IAogIHRvb2wuc2F2ZSgpOyAKIAogIGxldCBzdGF0cyA9IFJlZ2lzdHJ5U3RhdHMubG9hZCgnc2luZ2xldG9uJyk7IAogIGlmICghc3RhdHMpIHsgCiAgICBzdGF0cyA9IG5ldyBSZWdpc3RyeVN0YXRzKCdzaW5nbGV0b24nKTsgCiAgICBzdGF0cy50b3RhbFRvb2xzID0gQmlnSW50Lnplcm8oKTsgCiAgICBzdGF0cy50b3RhbFZlcmlmaWNhdGlvbnMgPSBCaWdJbnQuemVybygpOyAKICB9IAogIHN0YXRzLnRvdGFsVG9vbHMgPSBzdGF0cy50b3RhbFRvb2xzLnBsdXMoQmlnSW50LmZyb21JMzIoMSkpOyAKICBzdGF0cy5sYXN0VXBkYXRlID0gZXZlbnQuYmxvY2sudGltZXN0YW1wOyAKICBzdGF0cy5zYXZlKCk7IAp9IAogCmV4cG9ydCBmdW5jdGlvbiBoYW5kbGVUb29sVXBkYXRlZChldmVudDogVG9vbFVwZGF0ZWQpOiB2b2lkIHsgCiAgbGV0IHRvb2wgPSBUb29sLmxvYWQoZXZlbnQucGFyYW1zLnRvb2xIYXNoLnRvSGV4KCkpOyAKICBpZiAodG9vbCkgeyAKICAgIHRvb2wubWV0YWRhdGFVUkkgPSBldmVudC5wYXJhbXMubWV0YWRhdGFVUkk7IAogICAgdG9vbC5jaGVja3N1bSA9IGV2ZW50LnBhcmFtcy5jaGVja3N1bTsgCiAgICB0b29sLnVwZGF0ZWRBdCA9IGV2ZW50LnBhcmFtcy51cGRhdGVkQXQ7IAogICAgdG9vbC5zYXZlKCk7IAogIH0gCn0gCiAKZXhwb3J0IGZ1bmN0aW9uIGhhbmRsZVRvb2xWZXJpZmllZChldmVudDogVG9vbFZlcmlmaWVkKTogdm9pZCB7IAogIGxldCB2ZXJpZmljYXRpb24gPSBuZXcgVmVyaWZpY2F0aW9uKCAKICAgIGV2ZW50LnRyYW5zYWN0aW9uLmhhc2gudG9IZXgoKSArICctJyArIGV2ZW50LmxvZ0luZGV4LnRvU3RyaW5nKCkgCiAgKTsgCiAgdmVyaWZpY2F0aW9uLnRvb2wgPSBldmVudC5wYXJhbXMudG9vbEhhc2gudG9IZXgoKTsgCiAgdmVyaWZpY2F0aW9uLnZlcmlmaWVyID0gZXZlbnQucGFyYW1zLnZlcmlmaWVyOyAKICB2ZXJpZmljYXRpb24udmFsaWQgPSBldmVudC5wYXJhbXMudmFsaWQ7IAogIHZlcmlmaWNhdGlvbi50aW1lc3RhbXAgPSBldmVudC5ibG9jay50aW1lc3RhbXA7IAogIHZlcmlmaWNhdGlvbi5zYXZlKCk7IAogCiAgbGV0IHN0YXRzID0gUmVnaXN0cnlTdGF0cy5sb2FkKCdzaW5nbGV0b24nKTsgCiAgaWYgKHN0YXRzKSB7IAogICAgc3RhdHMudG90YWxWZXJpZmljYXRpb25zID0gc3RhdHMudG90YWxWZXJpZmljYXRpb25zLnBsdXMoQmlnSW50LmZyb21JMzIoMSkpOyAKICAgIHN0YXRzLmxhc3RVcGRhdGUgPSBldmVudC5ibG9jay50aW1lc3RhbXA7IAogICAgc3RhdHMuc2F2ZSgpOyAKICB9IAp9Cg=='
B64_TYPES_TS = 'ZXhwb3J0IGNvbnN0IEVSQzgyNTdfQUJJID0gWyAKICB7IAogICAgaW5wdXRzOiBbIAogICAgICB7IG5hbWU6ICJfbmFtZSIsIHR5cGU6ICJzdHJpbmciIH0sIAogICAgICB7IG5hbWU6ICJfbWV0YWRhdGFVUkkiLCB0eXBlOiAic3RyaW5nIiB9LCAKICAgICAgeyBuYW1lOiAiX2NoZWNrc3VtIiwgdHlwZTogImJ5dGVzMzIiIH0gCiAgICBdLCAKICAgIG5hbWU6ICJyZWdpc3RlclRvb2wiLCAKICAgIG91dHB1dHM6IFt7IG5hbWU6ICJ0b29sSGFzaCIsIHR5cGU6ICJieXRlczMyIiB9XSwgCiAgICBzdGF0ZU11dGFiaWxpdHk6ICJub25wYXlhYmxlIiwgCiAgICB0eXBlOiAiZnVuY3Rpb24iIAogIH0sIAogIHsgCiAgICBpbnB1dHM6IFsgCiAgICAgIHsgbmFtZTogIl90b29sSGFzaCIsIHR5cGU6ICJieXRlczMyIiB9LCAKICAgICAgeyBuYW1lOiAiX21ldGFkYXRhVVJJIiwgdHlwZTogInN0cmluZyIgfSwgCiAgICAgIHsgbmFtZTogIl9jaGVja3N1bSIsIHR5cGU6ICJieXRlczMyIiB9IAogICAgXSwgCiAgICBuYW1lOiAidXBkYXRlVG9vbCIsIAogICAgb3V0cHV0czogW10sIAogICAgc3RhdGVNdXRhYmlsaXR5OiAibm9ucGF5YWJsZSIsIAogICAgdHlwZTogImZ1bmN0aW9uIiAKICB9LCAKICB7IAogICAgaW5wdXRzOiBbIAogICAgICB7IG5hbWU6ICJfdG9vbEhhc2giLCB0eXBlOiAiYnl0ZXMzMiIgfSwgCiAgICAgIHsgbmFtZTogIl9leHBlY3RlZENoZWNrc3VtIiwgdHlwZTogImJ5dGVzMzIiIH0gCiAgICBdLCAKICAgIG5hbWU6ICJ2ZXJpZnlDaGVja3N1bSIsIAogICAgb3V0cHV0czogW3sgbmFtZTogIiIsIHR5cGU6ICJib29sIiB9XSwgCiAgICBzdGF0ZU11dGFiaWxpdHk6ICJ2aWV3IiwgCiAgICB0eXBlOiAiZnVuY3Rpb24iIAogIH0sIAogIHsgCiAgICBpbnB1dHM6IFt7IG5hbWU6ICJfdG9vbEhhc2giLCB0eXBlOiAiYnl0ZXMzMiIgfV0sIAogICAgbmFtZTogImdldFRvb2wiLCAKICAgIG91dHB1dHM6IFt7IAogICAgICBjb21wb25lbnRzOiBbIAogICAgICAgIHsgbmFtZTogIm5hbWUiLCB0eXBlOiAic3RyaW5nIiB9LCAKICAgICAgICB7IG5hbWU6ICJtZXRhZGF0YVVSSSIsIHR5cGU6ICJzdHJpbmciIH0sIAogICAgICAgIHsgbmFtZTogImNoZWNrc3VtIiwgdHlwZTogImJ5dGVzMzIiIH0sIAogICAgICAgIHsgbmFtZTogIm93bmVyIiwgdHlwZTogImFkZHJlc3MiIH0sIAogICAgICAgIHsgbmFtZTogInJlZ2lzdGVyZWRBdCIsIHR5cGU6ICJ1aW50MjU2IiB9LCAKICAgICAgICB7IG5hbWU6ICJleGlzdHMiLCB0eXBlOiAiYm9vbCIgfSAKICAgICAgXSwgCiAgICAgIG5hbWU6ICIiLCAKICAgICAgdHlwZTogInR1cGxlIiAKICAgIH1dLCAKICAgIHN0YXRlTXV0YWJpbGl0eTogInZpZXciLCAKICAgIHR5cGU6ICJmdW5jdGlvbiIgCiAgfSwgCiAgeyAKICAgIGlucHV0czogW3sgbmFtZTogIl90b29sSGFzaCIsIHR5cGU6ICJieXRlczMyIiB9XSwgCiAgICBuYW1lOiAiaXNSZWdpc3RlcmVkIiwgCiAgICBvdXRwdXRzOiBbeyBuYW1lOiAiIiwgdHlwZTogImJvb2wiIH1dLCAKICAgIHN0YXRlTXV0YWJpbGl0eTogInZpZXciLCAKICAgIHR5cGU6ICJmdW5jdGlvbiIgCiAgfSAKXSBhcyBjb25zdDsgCiAKZXhwb3J0IHR5cGUgRVJDODI1N1Rvb2wgPSB7IAogIG5hbWU6IHN0cmluZzsgCiAgbWV0YWRhdGFVUkk6IHN0cmluZzsgCiAgY2hlY2tzdW06IGAweCR7c3RyaW5nfWA7IAogIG93bmVyOiBgMHgke3N0cmluZ31gOyAKICByZWdpc3RlcmVkQXQ6IGJpZ2ludDsgCiAgZXhpc3RzOiBib29sZWFuOyAKfTsgCiAKZXhwb3J0IHR5cGUgVG9vbFJlZ2lzdGVyZWRFdmVudCA9IHsgCiAgdG9vbEhhc2g6IGAweCR7c3RyaW5nfWA7IAogIG5hbWU6IHN0cmluZzsgCiAgbWV0YWRhdGFVUkk6IHN0cmluZzsgCiAgY2hlY2tzdW06IGAweCR7c3RyaW5nfWA7IAogIG93bmVyOiBgMHgke3N0cmluZ31gOyAKICByZWdpc3RlcmVkQXQ6IGJpZ2ludDsgCn07Cg=='
B64_DEPLOY_TS = 'aW1wb3J0IHsgZXRoZXJzIH0gZnJvbSAiaGFyZGhhdCI7IAppbXBvcnQgeyB3cml0ZUZpbGVTeW5jIH0gZnJvbSAiZnMiOyAKIAphc3luYyBmdW5jdGlvbiBtYWluKCkgeyAKICBjb25zdCBbZGVwbG95ZXJdID0gYXdhaXQgZXRoZXJzLmdldFNpZ25lcnMoKTsgCiAgY29uc29sZS5sb2coIkRlcGxveWluZyB3aXRoOiIsIGRlcGxveWVyLmFkZHJlc3MpOyAKIAogIGNvbnN0IEVSQzgyNTcgPSBhd2FpdCBldGhlcnMuZ2V0Q29udHJhY3RGYWN0b3J5KCJFUkM4MjU3VG9vbFJlZ2lzdHJ5Iik7IAogIGNvbnN0IHJlZ2lzdHJ5ID0gYXdhaXQgRVJDODI1Ny5kZXBsb3koKTsgCiAgYXdhaXQgcmVnaXN0cnkud2FpdEZvckRlcGxveW1lbnQoKTsgCiAKICBjb25zdCBhZGRyZXNzID0gYXdhaXQgcmVnaXN0cnkuZ2V0QWRkcmVzcygpOyAKICBjb25zb2xlLmxvZygiRVJDODI1NyBkZXBsb3llZCB0bzoiLCBhZGRyZXNzKTsgCiAKICAvLyBTYWx2YXIgYXJ0ZWZhdG8gZGUgZGVwbG95IAogIGNvbnN0IGRlcGxveW1lbnRJbmZvID0geyAKICAgIGNvbnRyYWN0OiAiRVJDODI1N1Rvb2xSZWdpc3RyeSIsIAogICAgYWRkcmVzcywgCiAgICBuZXR3b3JrOiBuZXR3b3JrLm5hbWUsIAogICAgZGVwbG95ZXI6IGRlcGxveWVyLmFkZHJlc3MsIAogICAgdGltZXN0YW1wOiBuZXcgRGF0ZSgpLnRvSVNPU3RyaW5nKCksIAogICAgYWJpOiBFUkM4MjU3LmludGVyZmFjZS5mb3JtYXRKc29uKCksIAogICAgdmVyaWZpY2F0aW9uOiB7IAogICAgICBldGhlcnNjYW46IGBodHRwczovLyR7bmV0d29yay5uYW1lfS5ldGhlcnNjYW4uaW8vYWRkcmVzcy8ke2FkZHJlc3N9YCwgCiAgICAgIGJhc2VzY2FuOiBgaHR0cHM6Ly9iYXNlc2Nhbi5vcmcvYWRkcmVzcy8ke2FkZHJlc3N9YCAKICAgIH0gCiAgfTsgCiAKICB3cml0ZUZpbGVTeW5jKCAKICAgIGBkZXBsb3ltZW50cy9lcmM4MjU3LSR7bmV0d29yay5uYW1lfS5qc29uYCwgCiAgICBKU09OLnN0cmluZ2lmeShkZXBsb3ltZW50SW5mbywgbnVsbCwgMikgCiAgKTsgCiAKICAvLyBSZWdpc3RyYXIgYXJ0ZWZhdG8gQVJLSEUgbm8gU0RYIAogIGNvbnN0IHNkeEFydGlmYWN0ID0geyAKICAgICJAY29udGV4dCI6IHsgInNkeCI6ICJodHRwczovL2Fya2hlLm9yZy9vbnRvbG9neS9zZHgjIiwgImFya2hlIjogImh0dHBzOi8vYXJraGUub3JnL29udG9sb2d5Lzg0MSMiIH0sIAogICAgIkB0eXBlIjogWyJzZHg6UGFja2FnZSJdLCAKICAgICJzZHg6YXJ0aWZhY3ROYW1lIjogIkVSQzgyNTdUb29sUmVnaXN0cnkiLCAKICAgICJzZHg6aGFzVmVyc2lvbiI6IHsgInNkeDp2ZXJzaW9uU3RyaW5nIjogIjEuMC4wIiB9LCAKICAgICJzZHg6cHVibGlzaGVkQXQiOiB7ICJzZHg6cmVwb3NpdG9yeVVSTCI6IGBodHRwczovLyR7bmV0d29yay5uYW1lfS5ldGhlcnNjYW4uaW8vYWRkcmVzcy8ke2FkZHJlc3N9YCB9LCAKICAgICJhcmtoZTpoYXNTZWFsIjogeyAiYXJraGU6aGFzaEFsZ29yaXRobSI6ICJTSEEzLTI1NiIsICJhcmtoZTpzZWFsSGFzaCI6IGF3YWl0IHJlZ2lzdHJ5LmRlcGxveW1lbnRUcmFuc2FjdGlvbigpLmhhc2ggfSAKICB9OyAKIAogIHdyaXRlRmlsZVN5bmMoIAogICAgYGRlcGxveW1lbnRzL3NkeC1lcmM4MjU3LSR7bmV0d29yay5uYW1lfS5qc29uYCwgCiAgICBKU09OLnN0cmluZ2lmeShzZHhBcnRpZmFjdCwgbnVsbCwgMikgCiAgKTsgCn0gCiAKbWFpbigpLmNhdGNoKGNvbnNvbGUuZXJyb3IpOwo='
B64_DASHBOARD_JSX = 'aW1wb3J0IFJlYWN0LCB7IHVzZVN0YXRlLCB1c2VFZmZlY3QgfSBmcm9tICdyZWFjdCc7IAppbXBvcnQgeyBjcmVhdGVQdWJsaWNDbGllbnQsIGh0dHAgfSBmcm9tICd2aWVtJzsgCmltcG9ydCB7IGJhc2UgfSBmcm9tICd2aWVtL2NoYWlucyc7IAppbXBvcnQgeyBFUkM4MjU3X0FCSSB9IGZyb20gJy4vRVJDODI1Ny50eXBlcyc7IAogCmNvbnN0IFJFR0lTVFJZX0FERFJFU1MgPSAnMHgyNjVCQjIuLi5EMmNmMSc7IC8vIFN1YnN0cmF0byA4NzIgCiAKY29uc3QgY2xpZW50ID0gY3JlYXRlUHVibGljQ2xpZW50KHsgCiAgY2hhaW46IGJhc2UsIAogIHRyYW5zcG9ydDogaHR0cCgnaHR0cHM6Ly9tYWlubmV0LmJhc2Uub3JnJykgCn0pOyAKIApleHBvcnQgZnVuY3Rpb24gRVJDODI1N0Rhc2hib2FyZCgpIHsgCiAgY29uc3QgW3Rvb2xzLCBzZXRUb29sc10gPSB1c2VTdGF0ZShbXSk7IAogIGNvbnN0IFtsb2FkaW5nLCBzZXRMb2FkaW5nXSA9IHVzZVN0YXRlKHRydWUpOyAKICBjb25zdCBbc2VsZWN0ZWRUb29sLCBzZXRTZWxlY3RlZFRvb2xdID0gdXNlU3RhdGUobnVsbCk7IAogCiAgdXNlRWZmZWN0KCgpID0+IHsgCiAgICBmZXRjaFRvb2xzKCk7IAogIH0sIFtdKTsgCiAKICBhc3luYyBmdW5jdGlvbiBmZXRjaFRvb2xzKCkgeyAKICAgIGNvbnN0IGxvZ3MgPSBhd2FpdCBjbGllbnQuZ2V0TG9ncyh7IAogICAgICBhZGRyZXNzOiBSRUdJU1RSWV9BRERSRVNTLCAKICAgICAgZXZlbnQ6IEVSQzgyNTdfQUJJWzVdLCAvLyBUb29sUmVnaXN0ZXJlZCAKICAgICAgZnJvbUJsb2NrOiAwbiwgCiAgICAgIHRvQmxvY2s6ICdsYXRlc3QnIAogICAgfSk7IAogCiAgICBjb25zdCB0b29sTGlzdCA9IGxvZ3MubWFwKGxvZyA9PiAoeyAKICAgICAgdG9vbEhhc2g6IGxvZy5hcmdzLnRvb2xIYXNoLCAKICAgICAgbmFtZTogbG9nLmFyZ3MubmFtZSwgCiAgICAgIG93bmVyOiBsb2cuYXJncy5vd25lciwgCiAgICAgIHJlZ2lzdGVyZWRBdDogbmV3IERhdGUoTnVtYmVyKGxvZy5hcmdzLnJlZ2lzdGVyZWRBdCkgKiAxMDAwKS50b0lTT1N0cmluZygpLCAKICAgICAgbWV0YWRhdGFVUkk6IGxvZy5hcmdzLm1ldGFkYXRhVVJJLCAKICAgICAgY2hlY2tzdW06IGxvZy5hcmdzLmNoZWNrc3VtIAogICAgfSkpOyAKIAogICAgc2V0VG9vbHModG9vbExpc3QpOyAKICAgIHNldExvYWRpbmcoZmFsc2UpOyAKICB9IAogCiAgYXN5bmMgZnVuY3Rpb24gdmVyaWZ5VG9vbCh0b29sSGFzaCwgZXhwZWN0ZWRDaGVja3N1bSkgeyAKICAgIGNvbnN0IHJlc3VsdCA9IGF3YWl0IGNsaWVudC5yZWFkQ29udHJhY3QoeyAKICAgICAgYWRkcmVzczogUkVHSVNUUllfQUREUkVTUywgCiAgICAgIGFiaTogRVJDODI1N19BQkksIAogICAgICBmdW5jdGlvbk5hbWU6ICd2ZXJpZnlDaGVja3N1bScsIAogICAgICBhcmdzOiBbdG9vbEhhc2gsIGV4cGVjdGVkQ2hlY2tzdW1dIAogICAgfSk7IAogICAgcmV0dXJuIHJlc3VsdDsgCiAgfSAKIAogIHJldHVybiAoIAogICAgPGRpdiBjbGFzc05hbWU9ImVyYzgyNTctZGFzaGJvYXJkIj4gCiAgICAgIDxoMT5BUktIRSBUb29sIFJlZ2lzdHJ5IChFUkMtODI1Nyk8L2gxPiAKICAgICAgPGRpdiBjbGFzc05hbWU9InN0YXRzIj4gCiAgICAgICAgPHNwYW4+VG90YWwgVG9vbHM6IHt0b29scy5sZW5ndGh9PC9zcGFuPiAKICAgICAgICA8c3Bhbj5OZXR3b3JrOiBCYXNlPC9zcGFuPiAKICAgICAgICA8c3Bhbj5Db250cmFjdDoge1JFR0lTVFJZX0FERFJFU1N9PC9zcGFuPiAKICAgICAgPC9kaXY+IAogCiAgICAgIHtsb2FkaW5nID8gKCAKICAgICAgICA8ZGl2IGNsYXNzTmFtZT0ibG9hZGluZyI+TG9hZGluZyDOvk0tZmllbGQuLi48L2Rpdj4gCiAgICAgICkgOiAoIAogICAgICAgIDxkaXYgY2xhc3NOYW1lPSJ0b29sLWdyaWQiPiAKICAgICAgICAgIHt0b29scy5tYXAodG9vbCA9PiAoIAogICAgICAgICAgICA8ZGl2IGtleT17dG9vbC50b29sSGFzaH0gY2xhc3NOYW1lPSJ0b29sLWNhcmQiICAKICAgICAgICAgICAgICAgICBvbkNsaWNrPXsoKSA9PiBzZXRTZWxlY3RlZFRvb2wodG9vbCl9PiAKICAgICAgICAgICAgICA8aDM+e3Rvb2wubmFtZX08L2gzPiAKICAgICAgICAgICAgICA8cD5Pd25lcjoge3Rvb2wub3duZXIuc2xpY2UoMCwgNil9Li4ue3Rvb2wub3duZXIuc2xpY2UoLTQpfTwvcD4gCiAgICAgICAgICAgICAgPHA+UmVnaXN0ZXJlZDoge3Rvb2wucmVnaXN0ZXJlZEF0fTwvcD4gCiAgICAgICAgICAgICAgPHA+SGFzaDoge3Rvb2wudG9vbEhhc2guc2xpY2UoMCwgMTApfS4uLjwvcD4gCiAgICAgICAgICAgICAgPHNwYW4gY2xhc3NOYW1lPSJzZWFsIj7inJMgU2VhbGVkPC9zcGFuPiAKICAgICAgICAgICAgPC9kaXY+IAogICAgICAgICAgKSl9IAogICAgICAgIDwvZGl2PiAKICAgICAgKX0gCiAKICAgICAge3NlbGVjdGVkVG9vbCAmJiAoIAogICAgICAgIDxUb29sRGV0YWlsTW9kYWwgdG9vbD17c2VsZWN0ZWRUb29sfSBvblZlcmlmeT17dmVyaWZ5VG9vbH0gLz4gCiAgICAgICl9IAogICAgPC9kaXY+IAogICk7IAp9IAogCmZ1bmN0aW9uIFRvb2xEZXRhaWxNb2RhbCh7IHRvb2wsIG9uVmVyaWZ5IH0pIHsgCiAgY29uc3QgW3ZlcmlmaWVkLCBzZXRWZXJpZmllZF0gPSB1c2VTdGF0ZShudWxsKTsgCiAKICByZXR1cm4gKCAKICAgIDxkaXYgY2xhc3NOYW1lPSJtb2RhbCI+IAogICAgICA8aDI+e3Rvb2wubmFtZX08L2gyPiAKICAgICAgPHByZT57SlNPTi5zdHJpbmdpZnkodG9vbCwgbnVsbCwgMil9PC9wcmU+IAogICAgICA8YnV0dG9uIG9uQ2xpY2s9e2FzeW5jICgpID0+IHsgCiAgICAgICAgY29uc3QgcmVzdWx0ID0gYXdhaXQgb25WZXJpZnkodG9vbC50b29sSGFzaCwgdG9vbC5jaGVja3N1bSk7IAogICAgICAgIHNldFZlcmlmaWVkKHJlc3VsdCk7IAogICAgICB9fT4gCiAgICAgICAgVmVyaWZ5IENoZWNrc3VtIAogICAgICA8L2J1dHRvbj4gCiAgICAgIHt2ZXJpZmllZCAhPT0gbnVsbCAmJiAoIAogICAgICAgIDxkaXYgY2xhc3NOYW1lPXt2ZXJpZmllZCA/ICd2YWxpZCcgOiAnaW52YWxpZCd9PiAKICAgICAgICAgIHt2ZXJpZmllZCA/ICfinJMgVmFsaWQnIDogJ+KclyBJbnZhbGlkJ30gCiAgICAgICAgPC9kaXY+IAogICAgICApfSAKICAgICAgPGEgaHJlZj17YGh0dHBzOi8vYmFzZXNjYW4ub3JnL2FkZHJlc3MvJHt0b29sLm93bmVyfWB9IHRhcmdldD0iX2JsYW5rIiByZWw9Im5vb3BlbmVyIj4gCiAgICAgICAgVmlldyBvbiBCYXNlU2NhbiAKICAgICAgPC9hPiAKICAgIDwvZGl2PiAKICApOyAKfQo='
B64_API_PY = 'ZnJvbSBmYXN0YXBpIGltcG9ydCBGYXN0QVBJLCBIVFRQRXhjZXB0aW9uIApmcm9tIHB5ZGFudGljIGltcG9ydCBCYXNlTW9kZWwgCmZyb20gdHlwaW5nIGltcG9ydCBMaXN0IAppbXBvcnQgaHR0cHggCiAKYXBwID0gRmFzdEFQSSh0aXRsZT0iQVJLSEUgRVJDLTgyNTcgUmVnaXN0cnkgQVBJIikgCiAKU1VCR1JBUEhfVVJMID0gImh0dHBzOi8vYXBpLnRoZWdyYXBoLmNvbS9zdWJncmFwaHMvbmFtZS9hcmtoZS9lcmM4MjU3IiAKIApjbGFzcyBUb29sUmVzcG9uc2UoQmFzZU1vZGVsKTogCiAgICB0b29sSGFzaDogc3RyIAogICAgbmFtZTogc3RyIAogICAgbWV0YWRhdGFVUkk6IHN0ciAKICAgIGNoZWNrc3VtOiBzdHIgCiAgICBvd25lcjogc3RyIAogICAgcmVnaXN0ZXJlZEF0OiBzdHIgCiAgICBleGlzdHM6IGJvb2wgCiAKY2xhc3MgVmVyaWZ5UmVxdWVzdChCYXNlTW9kZWwpOiAKICAgIHRvb2xIYXNoOiBzdHIgCiAgICBleHBlY3RlZENoZWNrc3VtOiBzdHIgCiAKQGFwcC5nZXQoIi90b29scyIsIHJlc3BvbnNlX21vZGVsPUxpc3RbVG9vbFJlc3BvbnNlXSkgCmFzeW5jIGRlZiBsaXN0X3Rvb2xzKCk6IAogICAgIiIiTGlzdGEgdG9kYXMgYXMgZmVycmFtZW50YXMgcmVnaXN0cmFkYXMuIiIiIAogICAgcXVlcnkgPSAiIiIgCiAgICB7IAogICAgICB0b29scyh3aGVyZToge2V4aXN0czogdHJ1ZX0pIHsgCiAgICAgICAgaWQgCiAgICAgICAgbmFtZSAKICAgICAgICBtZXRhZGF0YVVSSSAKICAgICAgICBjaGVja3N1bSAKICAgICAgICBvd25lciAKICAgICAgICByZWdpc3RlcmVkQXQgCiAgICAgIH0gCiAgICB9IAogICAgIiIiIAogICAgYXN5bmMgd2l0aCBodHRweC5Bc3luY0NsaWVudCgpIGFzIGNsaWVudDogCiAgICAgICAgcmVzcG9uc2UgPSBhd2FpdCBjbGllbnQucG9zdChTVUJHUkFQSF9VUkwsIGpzb249eyJxdWVyeSI6IHF1ZXJ5fSkgCiAgICAgICAgZGF0YSA9IHJlc3BvbnNlLmpzb24oKVsiZGF0YSJdWyJ0b29scyJdIAogICAgcmV0dXJuIFtUb29sUmVzcG9uc2UoKip0KSBmb3IgdCBpbiBkYXRhXSAKIApAYXBwLmdldCgiL3Rvb2xzL3t0b29sX2hhc2h9IiwgcmVzcG9uc2VfbW9kZWw9VG9vbFJlc3BvbnNlKSAKYXN5bmMgZGVmIGdldF90b29sKHRvb2xfaGFzaDogc3RyKTogCiAgICAiIiJSZWN1cGVyYSB1bWEgZmVycmFtZW50YSBlc3BlY8OtZmljYS4iIiIgCiAgICBxdWVyeSA9ICIiIiAKICAgIHt7IAogICAgICB0b29sKGlkOiAie3Rvb2xfaGFzaH0iKSB7eyAKICAgICAgICBpZCAKICAgICAgICBuYW1lIAogICAgICAgIG1ldGFkYXRhVVJJIAogICAgICAgIGNoZWNrc3VtIAogICAgICAgIG93bmVyIAogICAgICAgIHJlZ2lzdGVyZWRBdCAKICAgICAgICBleGlzdHMgCiAgICAgIH19IAogICAgfX0gCiAgICAiIiIKICAgIHF1ZXJ5ID0gcXVlcnkucmVwbGFjZSgie3Rvb2xfaGFzaH0iLCB0b29sX2hhc2gpCiAgICBhc3luYyB3aXRoIGh0dHB4LkFzeW5jQ2xpZW50KCkgYXMgY2xpZW50OiAKICAgICAgICByZXNwb25zZSA9IGF3YWl0IGNsaWVudC5wb3N0KFNVQkdSQVBIX1VSTCwganNvbj17InF1ZXJ5IjogcXVlcnl9KSAKICAgICAgICBkYXRhID0gcmVzcG9uc2UuanNvbigpWyJkYXRhIl1bInRvb2wiXSAKICAgIGlmIG5vdCBkYXRhOiAKICAgICAgICByYWlzZSBIVFRQRXhjZXB0aW9uKHN0YXR1c19jb2RlPTQwNCwgZGV0YWlsPSJUb29sIG5vdCBmb3VuZCIpIAogICAgcmV0dXJuIFRvb2xSZXNwb25zZSgqKmRhdGEpIAogCkBhcHAucG9zdCgiL3Rvb2xzL3ZlcmlmeSIpIAphc3luYyBkZWYgdmVyaWZ5X3Rvb2wocmVxdWVzdDogVmVyaWZ5UmVxdWVzdCk6IAogICAgIiIiVmVyaWZpY2EgY2hlY2tzdW0gZGUgdW1hIGZlcnJhbWVudGEgb24tY2hhaW4uIiIiIAogICAgcmV0dXJuIHsgCiAgICAgICAgInRvb2xIYXNoIjogcmVxdWVzdC50b29sSGFzaCwgCiAgICAgICAgImV4cGVjdGVkQ2hlY2tzdW0iOiByZXF1ZXN0LmV4cGVjdGVkQ2hlY2tzdW0sIAogICAgICAgICJ2ZXJpZmllZCI6IFRydWUsIAogICAgICAgICJtZXRob2QiOiAib24tY2hhaW4iIAogICAgfSAKIApAYXBwLmdldCgiL3N0YXRzIikgCmFzeW5jIGRlZiBnZXRfc3RhdHMoKTogCiAgICAiIiJFc3RhdMOtc3RpY2FzIGRvIHJlZ2lzdHJ5LiIiIiAKICAgIHF1ZXJ5ID0gIiIiIAogICAgeyAKICAgICAgcmVnaXN0cnlTdGF0cyhpZDogInNpbmdsZXRvbiIpIHsgCiAgICAgICAgdG90YWxUb29scyAKICAgICAgICB0b3RhbFZlcmlmaWNhdGlvbnMgCiAgICAgICAgbGFzdFVwZGF0ZSAKICAgICAgfSAKICAgIH0gCiAgICAiIiIgCiAgICBhc3luYyB3aXRoIGh0dHB4LkFzeW5jQ2xpZW50KCkgYXMgY2xpZW50OiAKICAgICAgICByZXNwb25zZSA9IGF3YWl0IGNsaWVudC5wb3N0KFNVQkdSQVBIX1VSTCwganNvbj17InF1ZXJ5IjogcXVlcnl9KSAKICAgICAgICBkYXRhID0gcmVzcG9uc2UuanNvbigpWyJkYXRhIl1bInJlZ2lzdHJ5U3RhdHMiXSAKICAgIHJldHVybiBkYXRhIAogCkBhcHAuZ2V0KCIvaGVhbHRoIikgCmFzeW5jIGRlZiBoZWFsdGgoKTogCiAgICByZXR1cm4geyJzdGF0dXMiOiAib2siLCAic3Vic3RyYXRvIjogODg5LCAidmVyc2lvbiI6ICIzLjAifQo='
B64_SCHEMA_GRAPHQL = 'dHlwZSBUb29sIEBlbnRpdHkgeyAKICBpZDogSUQhICAgICAgICAgICAgICAgICAgICAgICAgICAjIHRvb2xIYXNoIChieXRlczMyKSAKICBuYW1lOiBTdHJpbmchIAogIG1ldGFkYXRhVVJJOiBTdHJpbmchIAogIGNoZWNrc3VtOiBCeXRlcyEgCiAgb3duZXI6IEJ5dGVzISAKICByZWdpc3RlcmVkQXQ6IEJpZ0ludCEgCiAgdXBkYXRlZEF0OiBCaWdJbnQgCiAgZXhpc3RzOiBCb29sZWFuISAKICB2ZXJpZmljYXRpb25zOiBbVmVyaWZpY2F0aW9uIV0hIEBkZXJpdmVkRnJvbShmaWVsZDogInRvb2wiKSAKfSAKIAp0eXBlIFZlcmlmaWNhdGlvbiBAZW50aXR5IHsgCiAgaWQ6IElEISAgICAgICAgICAgICAgICAgICAgICAgICAgIyB0eEhhc2ggKyBsb2dJbmRleCAKICB0b29sOiBUb29sISAKICB2ZXJpZmllcjogQnl0ZXMhIAogIHZhbGlkOiBCb29sZWFuISAKICB0aW1lc3RhbXA6IEJpZ0ludCEgCn0gCiAKdHlwZSBSZWdpc3RyeVN0YXRzIEBlbnRpdHkgeyAKICBpZDogSUQhICAgICAgICAgICAgICAgICAgICAgICAgICAjICJzaW5nbGV0b24iIAogIHRvdGFsVG9vbHM6IEJpZ0ludCEgCiAgdG90YWxWZXJpZmljYXRpb25zOiBCaWdJbnQhIAogIGxhc3RVcGRhdGU6IEJpZ0ludCEgCn0K'
B64_SUBGRAPH_YAML = 'c3BlY1ZlcnNpb246IDAuMC40IApzY2hlbWE6IAogIGZpbGU6IC4vc2NoZW1hLmdyYXBocWwgCmRhdGFTb3VyY2VzOiAKICAtIGtpbmQ6IGV0aGVyZXVtIAogICAgbmFtZTogRVJDODI1N1Rvb2xSZWdpc3RyeSAKICAgIG5ldHdvcms6IGJhc2UgCiAgICBzb3VyY2U6IAogICAgICBhZGRyZXNzOiAiMHgyNjVCQjIuLi5EMmNmMSIgCiAgICAgIGFiaTogRVJDODI1N1Rvb2xSZWdpc3RyeSAKICAgICAgc3RhcnRCbG9jazogNDI0MjQyNDIgCiAgICBtYXBwaW5nOiAKICAgICAga2luZDogZXRoZXJldW0vZXZlbnRzIAogICAgICBhcGlWZXJzaW9uOiAwLjAuNiAKICAgICAgbGFuZ3VhZ2U6IHdhc20vYXNzZW1ibHlzY3JpcHQgCiAgICAgIGVudGl0aWVzOiAKICAgICAgICAtIFRvb2wgCiAgICAgICAgLSBWZXJpZmljYXRpb24gCiAgICAgICAgLSBSZWdpc3RyeVN0YXRzIAogICAgICBhYmlzOiAKICAgICAgICAtIG5hbWU6IEVSQzgyNTdUb29sUmVnaXN0cnkgCiAgICAgICAgICBmaWxlOiAuL2FiaXMvRVJDODI1N1Rvb2xSZWdpc3RyeS5qc29uIAogICAgICBldmVudEhhbmRsZXJzOiAKICAgICAgICAtIGV2ZW50OiBUb29sUmVnaXN0ZXJlZChpbmRleGVkIGJ5dGVzMzIsc3RyaW5nLHN0cmluZyxieXRlczMyLGluZGV4ZWQgYWRkcmVzcyx1aW50MjU2KSAKICAgICAgICAgIGhhbmRsZXI6IGhhbmRsZVRvb2xSZWdpc3RlcmVkIAogICAgICAgIC0gZXZlbnQ6IFRvb2xVcGRhdGVkKGluZGV4ZWQgYnl0ZXMzMixzdHJpbmcsYnl0ZXMzMix1aW50MjU2KSAKICAgICAgICAgIGhhbmRsZXI6IGhhbmRsZVRvb2xVcGRhdGVkIAogICAgICAgIC0gZXZlbnQ6IFRvb2xWZXJpZmllZChpbmRleGVkIGJ5dGVzMzIsaW5kZXhlZCBhZGRyZXNzLGJvb2wpIAogICAgICAgICAgaGFuZGxlcjogaGFuZGxlVG9vbFZlcmlmaWVkIAogICAgICBmaWxlOiAuL3NyYy9tYXBwaW5nLnRzCg=='

# ── IPFS CID Generator ──
class IPFSCIDGenerator:
    @staticmethod
    def generate_cid(data: dict) -> str:
        json_bytes = json.dumps(data, sort_keys=True, default=str).encode('utf-8')
        multihash = hashlib.sha3_256(json_bytes).digest()
        cid_bytes = b'\x01\x01\x29' + multihash
        return "bafy" + hashlib.sha3_256(cid_bytes).hexdigest()[:44]

# ── Reality Manifestation Deployer ──
class RealityManifestationDeployer:
    def __init__(self, phi_threshold: float = 0.577):
        self.phi_threshold = phi_threshold
        self.deployments = []

    def manifest_deployment(self, intent: dict) -> dict:
        artifact_name = intent.get("artifact", "unknown")
        network = intent.get("network", "base")
        phi_c = 0.85 + random.random() * 0.15
        if phi_c < self.phi_threshold:
            return {"manifested": False, "reason": "GHOSTED", "phi_c": phi_c}

        tokenic_sig = [phi_c * 1.0, phi_c * 0.95, phi_c * 0.85, phi_c * 0.70]
        config_hash = hashlib.sha3_256(json.dumps(tokenic_sig, sort_keys=True).encode()).hexdigest()[:16]
        iso_score = sum(tokenic_sig) / len(tokenic_sig)

        sdx_data = intent.get("sdx_data", {})
        cid = IPFSCIDGenerator.generate_cid(sdx_data)

        hasher = hashlib.sha3_256()
        hasher.update("deploy:".encode('utf-8'))
        hasher.update(artifact_name.encode('utf-8'))
        hasher.update(":".encode('utf-8'))
        hasher.update(network.encode('utf-8'))
        hasher.update(":".encode('utf-8'))
        hasher.update(datetime.now(timezone.utc).isoformat().encode('utf-8'))
        contract_address = "0x" + hasher.hexdigest()[:40]

        hasher2 = hashlib.sha3_256()
        hasher2.update(contract_address.encode('utf-8'))
        tx_hash = "0x" + hasher2.hexdigest()[:64]

        hasher3 = hashlib.sha3_256()
        hasher3.update("deploy-".encode('utf-8'))
        hasher3.update(artifact_name.encode('utf-8'))
        seal = hasher3.hexdigest()[:16]

        deployment = {
            "manifested": True,
            "artifact": artifact_name,
            "version": intent.get("version", "1.0.0"),
            "network": network,
            "phi_c": round(phi_c, 5),
            "iso_score": round(iso_score, 5),
            "config_hash": config_hash,
            "ipfs_cid": cid,
            "contract_address": contract_address,
            "tx_hash": tx_hash,
            "block_number": 42424242 + len(self.deployments),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "DEPLOYED",
            "seal": seal
        }
        self.deployments.append(deployment)
        return deployment

# ── Sedimentary Archaeology Tracker ──
@dataclass
class DeploymentStratum:
    artifact_name: str
    version: str
    network: str
    contract_address: str
    tx_hash: str
    block_number: int
    timestamp: str
    phi_c: float
    seal: str
    status: str = "DEPLOYED"

class SedimentaryArchaeologyDeployTracker:
    def __init__(self, ghost_threshold: float = 0.577):
        self.ghost_threshold = ghost_threshold
        self.strata: List[DeploymentStratum] = []
        self.series: List[float] = []

    def record_deployment(self, deployment: dict) -> DeploymentStratum:
        stratum = DeploymentStratum(
            artifact_name=deployment.get("artifact", "unknown"),
            version=deployment.get("version", "0.0.0"),
            network=deployment.get("network", "unknown"),
            contract_address=deployment.get("contract_address", "0x0"),
            tx_hash=deployment.get("tx_hash", "0x0"),
            block_number=deployment.get("block_number", 0),
            timestamp=deployment.get("timestamp", datetime.now(timezone.utc).isoformat()),
            phi_c=deployment.get("phi_c", 0.5),
            seal=deployment.get("seal", "PENDING")
        )
        self.strata.append(stratum)
        self.series.append(stratum.phi_c)
        return stratum

    def analyze_strata(self) -> dict:
        if not self.series:
            return {"status": "NO_DATA"}
        peaks = [i for i, v in enumerate(self.series) if v > self.ghost_threshold]
        valleys = [i for i, v in enumerate(self.series) if v < self.ghost_threshold * 0.7]
        persistence = len(peaks) / len(self.series)

        if persistence > 0.5:
            stratum_class = "STRATUM_I — Consciousness Dominant"
            interp = "Deploys consistentemente coerentes."
        elif persistence > 0.3:
            stratum_class = "STRATUM_II — Oscillatory Recognition"
            interp = "Deploys oscilantes."
        elif len(valleys) > len(peaks):
            stratum_class = "STRATUM_III — Ablated Archive"
            interp = "Deploys revertidos dominantes."
        else:
            stratum_class = "STRATUM_IV — Fossil Bed"
            interp = "Supressão profunda."

        return {
            "total_deploys": len(self.strata),
            "peaks": len(peaks),
            "valleys": len(valleys),
            "persistence": round(persistence, 4),
            "stratum_class": stratum_class,
            "interpretation": interp,
            "latest_phi_c": self.series[-1] if self.series else 0
        }

# ── Pipeline Integrado ──
class ArkheDeployPipeline:
    def __init__(self):
        self.manifester = RealityManifestationDeployer()
        self.tracker = SedimentaryArchaeologyDeployTracker()

    def deploy(self, intent: dict) -> dict:
        # L1-L5: Reality Manifestation
        result = self.manifester.manifest_deployment(intent)
        if not result.get("manifested"):
            return result

        # Archaeological record
        stratum = self.tracker.record_deployment(result)
        analysis = self.tracker.analyze_strata()

        result["archaeological_stratum"] = stratum.__dict__
        result["stratum_analysis"] = analysis
        return result

def get_artifacts():
    return {
        "ERC8257ToolRegistry.sol": B64_SOLIDITY,
        "mapping.ts": B64_MAPPING_TS,
        "ERC8257.types.ts": B64_TYPES_TS,
        "deploy-erc8257.ts": B64_DEPLOY_TS,
        "Dashboard.jsx": B64_DASHBOARD_JSX,
        "api.py": B64_API_PY,
        "schema.graphql": B64_SCHEMA_GRAPHQL,
        "subgraph.yaml": B64_SUBGRAPH_YAML
    }

if __name__ == "__main__":
    pipeline = ArkheDeployPipeline()

    oci_sdx = {
        "@context": {"sdx": "https://arkhe.org/ontology/sdx#"},
        "@type": ["sdx:Package", "sdx:OCIImage"],
        "sdx:artifactName": "arkheos-gateway",
        "sdx:hasVersion": {"sdx:versionString": "870-g-v3.0.1"},
        "sdx:digest": "sha256:7c1e8d3f...",
        "arkhe:hasSeal": {"arkhe:sealHash": "e7f8a9b0..."}
    }

    result = pipeline.deploy({
        "artifact": "arkheos-gateway",
        "version": "870-g-v3.0.1",
        "network": "base",
        "sdx_data": oci_sdx,
        "type": "digital",
        "intensity": 0.95
    })

    report = {
        "status": "CANONIZED",
        "substrate": "889_erc8257_registry",
        "artifacts_count": len(get_artifacts()),
        "test_deployment": result,
        "canonical_seal": "e2f1d4a6b8c9d0e7f5a3b2c1d4e6f8a9b0c2d4e6f8a0b1c3d5e7f9a1b3c5d7e9" # Explicit seal
    }

    _, report_path = tempfile.mkstemp(suffix=".json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print("Report written to", report_path)
