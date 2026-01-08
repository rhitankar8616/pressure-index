"""
How It Works Page
Explanation of Pressure Index methodology
"""

import streamlit as st
import os
import sys
import base64

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.components.ui_components import render_footer


def display_pdf(pdf_path):
    """Display a PDF file in the Streamlit app"""

    # Check if file exists
    if not os.path.exists(pdf_path):
        st.error(f"PDF file not found at: {pdf_path}")
        st.info("Please place your research paper PDF in the 'data' folder")
        return

    # Read PDF file
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # Display PDF using Streamlit's native components
    # Create an expander for better UX
    with st.expander("📄 View Research Paper", expanded=True):
        # Use Streamlit's experimental PDF viewer
        try:
            # Try to display using streamlit components
            import streamlit.components.v1 as components

            # Encode PDF to base64
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')

            # Use PDF.js viewer with object tag (more compatible)
            pdf_display = f'''
            <style>
            .pdf-container {{
                width: 100%;
                height: 1200px;
                border: 2px solid #1e293b;
                border-radius: 8px;
                overflow: hidden;
            }}
            </style>
            <div class="pdf-container">
                <object
                    data="data:application/pdf;base64,{base64_pdf}"
                    type="application/pdf"
                    width="100%"
                    height="100%">
                    <embed
                        src="data:application/pdf;base64,{base64_pdf}"
                        type="application/pdf"
                        width="100%"
                        height="100%" />
                </object>
            </div>
            '''

            components.html(pdf_display, height=1220, scrolling=True)

        except Exception as e:
            st.error(f"Error displaying PDF: {str(e)}")
            st.info("The PDF file exists but cannot be displayed in your browser. This is a browser compatibility issue.")


def render_how_it_works():
    """Render the How It Works page"""

    st.markdown("""
    Pressure Index (PI) is a ball-by-ball metric designed to quantify the pressure experienced
    by a team while batting second in a limited-overs cricket match. Based on the foundation laid
    by H.H Lemmer and Dibyojyoti Bhattacharjee (2016) and several subsequent extended works over
    the years, the current study by Rhitankar Bandyopadhyay and Dibyojyoti Bhattacharjee (2025)
    focuses on phasewise third order Markov models and Gamma distribution fallbacks to strategize
    controlled run chases in T20 cricket.

    **Read the full research paper below:**
    """)

    st.markdown("---")

    # PDF Display
    # Get the path to the PDF file (should be in the 'data' folder)
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pdf_path = os.path.join(base_path, 'data', 'Applications_of_higher_order_Markov_models_and_Pressure_Index_to_strategize_controlled_run_chases_in_Twenty20_cricket.pdf')

    # Display the PDF
    display_pdf(pdf_path)


if __name__ == "__main__":
    render_how_it_works()
