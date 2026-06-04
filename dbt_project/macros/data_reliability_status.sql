{% macro data_reliability_status(trust_score_col, open_incident_count_col, highest_open_severity_col) %}
    case
        when {{ trust_score_col }} < 0.65
            or {{ highest_open_severity_col }} = 'CRITICAL'
            then 'DO NOT USE'

        when {{ trust_score_col }} >= 0.85
            and {{ open_incident_count_col }} = 0
            then 'TRUSTED'

        when {{ trust_score_col }} >= 0.65
            or (
                {{ open_incident_count_col }} <= 2
                and coalesce({{ highest_open_severity_col }}, 'NONE') != 'CRITICAL'
            )
            then 'USE WITH CAUTION'

        else 'DO NOT USE'
    end
{% endmacro %}