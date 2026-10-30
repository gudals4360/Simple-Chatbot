# Third-party notices / 외부 데이터 출처 및 라이선스

## NVIDIA Nemotron-Personas-Korea

- 제작자 / Data developer: **NVIDIA Corporation**
- 데이터셋명: **Nemotron-Personas-Korea**
- 공식 원본: https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea
- 공식 데이터셋 카드: https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea/blob/main/README.md
- 라이선스: **Creative Commons Attribution 4.0 International (CC BY 4.0)**
- 라이선스 안내: https://creativecommons.org/licenses/by/4.0/
- 라이선스 전문: https://creativecommons.org/licenses/by/4.0/legalcode
- 출처·라이선스 확인일: 2026-10-30

### 사용 범위와 변경 사항

이 프로젝트는 위 합성 데이터셋에서 이지아, 박승범, 박한솔, 최선동, 박윤아 5명의 페르소나를 선별하여 챗봇의 배경 정보로 사용합니다. 원본 전체를 그대로 배포하는 것이 아니라, 필요한 필드를 선택·재구성하여 JSON 및 대화용 설정에 반영했습니다. 회사·직장 설정, 말투, 인사, 추천 질문, 상태 메시지, 아바타 등은 프로젝트에서 추가하거나 변경한 내용입니다. 원본 데이터와 프로젝트에서 만든 설정을 실제 인물의 정보나 실제 인터뷰 결과로 해석해서는 안 됩니다.

적용 범위는 `Simple Chat bot/backend/data/personas.json`의 위 5명과, `Simple Chat bot/standalone.html` 및 `netlify/functions/chat-api.mjs`에 포함된 해당 페르소나 데이터입니다. 이 고지는 해당 데이터의 사본이나 가공본을 재배포할 때 함께 유지해야 합니다.

저장소에 보존된 원본 식별자:

| 페르소나 | UUID |
|---|---|
| 이지아 | `d0753c0b64024b468f1c9f7153f86310` |
| 박승범 | `d6d1e3542a504d298ccd03110490beb3` |
| 박한솔 | `dcea5f5ae75f461387149166e3ee6539` |
| 최선동 | `dc3fb3f53ebb4f7b98d813c9c798622a` |
| 박윤아 | `6b02719bab6645ba83f077320695cf7d` |

### 라이선스 고지

The persona material identified above is adapted from **Nemotron-Personas-Korea**, developed by **NVIDIA Corporation**, and is provided under the **Creative Commons Attribution 4.0 International License (CC BY 4.0)**. Source: https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea. License: https://creativecommons.org/licenses/by/4.0/. This project selected and reformatted records and added or modified chatbot-specific settings as described above.

재사용·재배포 시 제작자와 원본 출처, 라이선스 링크를 유지하고 변경 여부를 표시해야 합니다. NVIDIA가 이 프로젝트를 후원하거나 보증한다는 의미는 아닙니다. 원본은 합성 데이터이며 보증 없이 제공됩니다. 이 고지는 위 외부 데이터에 대한 것으로, 저장소의 다른 코드·자료 전체에 CC BY 4.0을 부여하지 않습니다.
