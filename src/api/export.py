"""
API routes for exporting cluster data.
"""
from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse
from typing import List, Dict
import pandas as pd
import io
from datetime import datetime
from src.database import cluster_store
from src.services import vlan_sync_service


router = APIRouter(prefix="/api/export", tags=["export"])


def prepare_cluster_data() -> List[Dict]:
    """Prepare all cluster data for export."""
    # Get VLAN Manager synced data
    vlan_data = vlan_sync_service.load_from_cache()
    
    # Get manual clusters
    manual_clusters = cluster_store.get_all_clusters()
    
    # Combine all clusters
    all_clusters = []
    if vlan_data:
        all_clusters.extend(vlan_data.get("clusters", []))
    all_clusters.extend(manual_clusters)
    
    # Flatten cluster data for export
    export_data = []
    for cluster in all_clusters:
        export_data.append({
            "Cluster Name": cluster.get("clusterName", ""),
            "Site": cluster.get("site", ""),
            "Domain": cluster.get("domainName", ""),
            "Segments": ", ".join(cluster.get("segments", [])),
            "Segment Count": len(cluster.get("segments", [])),
            "Console URL": cluster.get("consoleUrl", ""),
            "Source": cluster.get("source", "manual"),
            "Created At": cluster.get("createdAt", ""),
            "ID": cluster.get("id", "")
        })
    
    return export_data


@router.get(
    "/csv",
    summary="Export clusters as CSV"
)
async def export_csv():
    """
    Export all clusters as CSV file.
    """
    try:
        data = prepare_cluster_data()
        df = pd.DataFrame(data)
        
        # Create CSV in memory
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Generate filename with timestamp
        filename = f"clusters-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get(
    "/excel",
    summary="Export clusters as Excel"
)
async def export_excel():
    """
    Export all clusters as Excel file (.xlsx).
    """
    try:
        data = prepare_cluster_data()
        df = pd.DataFrame(data)
        
        # Create Excel in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Clusters')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Clusters']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
        
        output.seek(0)
        
        # Generate filename with timestamp
        filename = f"clusters-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx"
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

