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
        st.info("Please place your research paper PDF in the 'data' folder and name it 'research_paper.pdf'")
        return

    # Read and encode PDF
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    # Embed PDF in iframe with full width
    pdf_display = f"""
    <iframe
        src="data:application/pdf;base64,{base64_pdf}"
        width="100%"
        height="1200px"
        type="application/pdf"
        style="border: 1px solid #1e293b; border-radius: 8px;"
    >
        <p>Your browser does not support PDFs.
        <a href="data:application/pdf;base64,{base64_pdf}" download="research_paper.pdf">
        Download the PDF</a> instead.</p>
    </iframe>
    """

    st.markdown(pdf_display, unsafe_allow_html=True)


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
