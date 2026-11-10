#!/usr/bin/env python3
"""
PoC Traffic Simulator for Token Tracker
Demonstrates:
  1. Normal departmental API traffic (Within Budget)
  2. 80% Soft Alert Warning threshold
  3. 100% Hard Limit Block (HTTP 429 response)
"""
import sys
from app.services.gatekeeper import estimate_tokens, calculate_estimated_cost, format_error_response


class MockDatabase:
    """Mock database with department budgets to simulate real-time Redis/Timescale checks"""
    def __init__(self):
        self.budgets = {
            "dept-ti-01": {"limit": 1500.0, "used": 200.0},
            "dept-mkt-02": {"limit": 600.0, "used": 490.0},    # >80% threshold ($480)
            "dept-rh-03": {"limit": 250.0, "used": 250.00},    # Reached 100% threshold ($250)
        }

    async def check_budget(self, entity_id: str, estimated_cost: float):
        entry = self.budgets.get(entity_id)
        if not entry:
            return {"allowed": True}

        limit = entry["limit"]
        used = entry["used"]
        projected = used + estimated_cost

        if projected > limit:
            return {
                "allowed": False,
                "reason": f"Budget limit (${limit:.2f}) exceeded for {entity_id}. Current: ${used:.2f}, Est: ${estimated_cost:.4f}",
            }

        warning = projected >= (limit * 0.8)
        return {"allowed": True, "warning": warning, "projected": projected}


def simulate_poc():
    print("=== INICIANDO SIMULAÇÃO DA POC: TOKEN TRACKER (FinOps) ===")
    mock_db = MockDatabase()

    # 1. Requisição Departamento TI (Dentro do Orçamento)
    ti_request = {
        "model": "claude-3-haiku-20240307",
        "messages": [{"role": "user", "content": "Script de automação para deploy em Kubernetes."}],
    }
    ti_tokens = estimate_tokens(ti_request)
    ti_cost = calculate_estimated_cost("claude", ti_request["model"], ti_tokens)
    print(f"\n[CENÁRIO 1: TI - Normal]")
    print(f"  Tokens Estimados: {ti_tokens} | Custo Estimado: ${ti_cost:.6f}")

    entry = mock_db.budgets["dept-ti-01"]
    status_ti = (entry["used"] + ti_cost) <= entry["limit"]
    print(f"  Resultado: {'PERMITIDO (200 OK)' if status_ti else 'BLOQUEADO'}")
    assert status_ti is True

    # 2. Requisição Marketing (Alerta Preventivo 80%)
    mkt_request = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "Criação de copy para campanha promocional de Q2."}],
    }
    mkt_tokens = estimate_tokens(mkt_request)
    mkt_cost = calculate_estimated_cost("claude", mkt_request["model"], mkt_tokens)
    entry_mkt = mock_db.budgets["dept-mkt-02"]
    projected_mkt = entry_mkt["used"] + mkt_cost
    is_warning = projected_mkt >= (entry_mkt["limit"] * 0.8)
    print(f"\n[CENÁRIO 2: Marketing - Alerta 80% Quota]")
    print(f"  Uso Atual: ${entry_mkt['used']:.2f} / ${entry_mkt['limit']:.2f} ({(entry_mkt['used']/entry_mkt['limit'])*100:.1f}%)")
    print(f"  Sinalização de Alerta (Soft Limit): {'ATIVADA' if is_warning else 'DESATIVADA'}")
    assert is_warning is True

    # 3. Requisição RH (Bloqueio Preventivo 100% - Hard Cap)
    rh_request = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "Triagem em lote de 500 currículos em PDF com extração completa."}],
    }
    rh_tokens = estimate_tokens(rh_request)
    rh_cost = calculate_estimated_cost("claude", rh_request["model"], rh_tokens)
    entry_rh = mock_db.budgets["dept-rh-03"]
    projected_rh = entry_rh["used"] + rh_cost
    blocked = projected_rh > entry_rh["limit"]

    print(f"\n[CENÁRIO 3: Recursos Humanos - Bloqueio Ativo]")
    print(f"  Uso Atual: ${entry_rh['used']:.2f} / Teto: ${entry_rh['limit']:.2f} | Custo da Requisição: ${rh_cost:.4f}")
    if blocked:
        err = format_error_response("claude", f"Budget limit (${entry_rh['limit']:.2f}) exceeded.")
        print(f"  Status Retornado: HTTP 429 Too Many Requests")
        print(f"  Payload Interceptado: {err}")
    assert blocked is True

    print("\n=== SIMULAÇÃO CONCLUÍDA COM SUCESSO: TODOS OS CENÁRIOS FORAM VALIDADOS! ===")


if __name__ == "__main__":
    simulate_poc()
