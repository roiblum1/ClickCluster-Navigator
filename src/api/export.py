"""
API routes for exporting cluster data.
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from typing import List, Dict
import pandas as pd
import io
from datetime import datetime
from src.services.export_service import export_service


router = APIRouter(prefix="/api/export", tags=["export"])


@router.get(
    "/csv",
    summary="Export clusters as CSV"
)
async def export_csv():
    """
    Export all clusters as CSV file.
    """
    try:
        data = export_service.prepare_cluster_data()
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
        data = export_service.prepare_cluster_data()
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

