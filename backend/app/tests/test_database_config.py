from app.core.database import _is_supabase_managed_host


def test_is_supabase_managed_host_matches_pooler_domains():
    assert _is_supabase_managed_host("db.example.supabase.co") is True
    assert _is_supabase_managed_host("aws-0-ap-southeast-1.pooler.supabase.com") is True
    assert _is_supabase_managed_host("project-ref.supabase.com") is True


def test_is_supabase_managed_host_ignores_non_supabase_domains():
    assert _is_supabase_managed_host("localhost") is False
    assert _is_supabase_managed_host("db.internal.example.com") is False


def test_is_supabase_managed_host_matches_alembic_pooler_hosts():
    assert _is_supabase_managed_host("db.abcdefg.supabase.com") is True
    assert _is_supabase_managed_host("aws-0-us-east-1.pooler.supabase.com") is True
