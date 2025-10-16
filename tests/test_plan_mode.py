"""
Tests para el sistema de plan mode.
"""
import pytest
from cli.plan_mode import PlanMode, PlanAction, ActionType, ExecutionPlan

def test_plan_creation():
    plan_mode = PlanMode()
    
    class MockContext:
        pass
    
    plan = plan_mode.create_plan_from_intent("modifica el archivo test.py", MockContext())
    
    assert isinstance(plan, ExecutionPlan)
    assert len(plan.actions) > 0
    assert any(a.type == ActionType.EDIT_FILE for a in plan.actions)

def test_plan_with_git():
    plan_mode = PlanMode()
    
    class MockContext:
        pass
    
    plan = plan_mode.create_plan_from_intent("hacer commit de los cambios", MockContext())
    
    assert isinstance(plan, ExecutionPlan)
    assert any(a.type == ActionType.GIT_OPERATION for a in plan.actions)

def test_plan_with_shell():
    plan_mode = PlanMode()
    
    class MockContext:
        pass
    
    plan = plan_mode.create_plan_from_intent("ejecuta npm install", MockContext())
    
    assert isinstance(plan, ExecutionPlan)
    assert any(a.type == ActionType.EXECUTE_SHELL for a in plan.actions)

def test_plan_string_representation():
    plan = ExecutionPlan(
        title="Test Plan",
        actions=[
            PlanAction(
                type=ActionType.READ_FILE,
                description="Leer archivo",
                target="test.py",
                risk_level="low"
            )
        ]
    )
    
    plan_str = str(plan)
    assert "Test Plan" in plan_str
    assert "Leer archivo" in plan_str
    assert "📋" in plan_str

def test_plan_action_str():
    action = PlanAction(
        type=ActionType.EDIT_FILE,
        description="Editar archivo",
        target="test.py",
        risk_level="medium"
    )
    
    action_str = str(action)
    assert "Editar archivo" in action_str
    assert "⚠️" in action_str

def test_plan_history():
    plan_mode = PlanMode()
    
    plan = ExecutionPlan(
        title="Test",
        actions=[]
    )
    
    class MockContext:
        pass
    
    plan_mode.execute_plan(plan, MockContext())
    
    assert len(plan_mode.plan_history) == 1

def test_plan_approval_requirement():
    plan_low_risk = ExecutionPlan(
        title="Low Risk Plan",
        actions=[
            PlanAction(
                type=ActionType.READ_FILE,
                description="Read",
                target="test.py",
                risk_level="low"
            )
        ]
    )
    
    plan_high_risk = ExecutionPlan(
        title="High Risk Plan",
        actions=[
            PlanAction(
                type=ActionType.EXECUTE_SHELL,
                description="Execute",
                target="rm -rf",
                risk_level="high"
            )
        ]
    )
    
    assert plan_low_risk.requires_approval == True
    assert plan_high_risk.requires_approval == True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
