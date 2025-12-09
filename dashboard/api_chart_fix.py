@app.get("/api/chart-data", response_model=Dict[str, Any])
async def get_chart_data(
    from_date: Optional[str] = Query(None, description="Start date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    database: DatabaseManager = Depends(get_db)
):
    """
    Get simplified time-series data for dashboard charts

    Returns aggregated time-series data for visualizations:
    - Daily validation counts
    - Success/failure rates
    - Citation metrics
    - Provider distribution

    Query Parameters:
    - from_date: Filter validations created after this date (ISO 8601)
    - to_date: Filter validations created before this date (ISO 8601)

    Returns:
    - Dictionary with daily data and provider distribution
    """
    # Input validation
    validate_date_format(from_date, "from_date")
    validate_date_format(to_date, "to_date")
    validate_date_range(from_date, to_date)

    try:
        # Simple aggregation query
        query = """
            SELECT
                DATE(created_at) as date,
                COUNT(*) as total_validations,
                COUNT(CASE WHEN validation_status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN validation_status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN validation_status = 'pending' THEN 1 END) as pending,
                SUM(CASE WHEN validation_status = 'completed' THEN citation_count ELSE 0 END) as successful_citations,
                SUM(CASE WHEN validation_status = 'failed' THEN citation_count ELSE 0 END) as failed_citations,
                SUM(citation_count) as total_citations,
                COUNT(CASE WHEN provider = 'model_a' OR provider = 'openai' THEN 1 END) as model_a_jobs,
                COUNT(CASE WHEN provider = 'model_b' OR provider = 'gemini' THEN 1 END) as model_b_jobs
            FROM validations
            WHERE 1=1
        """
        params = []

        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date)

        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date)

        query += " GROUP BY DATE(created_at) ORDER BY date ASC"

        cursor = database.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to list of dicts
        daily_data = []
        for row in rows:
            daily_data.append({
                "date": row[0],
                "total_validations": row[1],
                "completed": row[2],
                "failed": row[3],
                "pending": row[4],
                "successful_citations": row[5] or 0,
                "failed_citations": row[6] or 0,
                "total_citations": row[7] or 0,
                "model_a_jobs": row[8] or 0,
                "model_b_jobs": row[9] or 0
            })

        # Also get provider distribution
        provider_query = """
            SELECT provider, COUNT(*) as count
            FROM validations
            WHERE 1=1
        """
        provider_params = []

        if from_date:
            provider_query += " AND created_at >= ?"
            provider_params.append(from_date)

        if to_date:
            provider_query += " AND created_at <= ?"
            provider_params.append(to_date)

        provider_query += " GROUP BY provider"

        cursor.execute(provider_query, provider_params)
        provider_rows = cursor.fetchall()

        provider_data = {}
        for row in provider_rows:
            provider = row[0] or 'unknown'
            provider_data[provider] = row[1]

        return {"daily": daily_data, "providers": provider_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chart data: {str(e)}")