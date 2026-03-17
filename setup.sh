#!/bin/bash

# WhatsApp Chat Analyzer - Complete Setup Script
# This script will set up and run the WhatsApp Chat Analyzer application

echo "========================================="
echo "  WhatsApp Chat Analyzer - Setup Script  "
echo "========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Windows (Git Bash)
check_windows() {
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ -n "$WINDIR" ]]; then
        return 0  # It's Windows
    else
        return 1  # It's Linux/Mac
    fi
}

# Create virtual environment based on OS
create_venv() {
    print_message "Creating virtual environment..."
    
    if check_windows; then
        # Windows (Git Bash)
        python -m venv venv
        if [ $? -ne 0 ]; then
            print_error "Failed to create virtual environment. Make sure Python is installed and in PATH."
            exit 1
        fi
        print_success "Virtual environment created successfully"
        print_message "Activating virtual environment..."
        source venv/Scripts/activate
    else
        # Linux/Mac
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            print_error "Failed to create virtual environment. Make sure Python3 is installed."
            exit 1
        fi
        print_success "Virtual environment created successfully"
        print_message "Activating virtual environment..."
        source venv/bin/activate
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Virtual environment activated"
    else
        print_error "Failed to activate virtual environment"
        exit 1
    fi
}

# Check Python version
check_python() {
    print_message "Checking Python version..."
    
    if check_windows; then
        python_version=$(python --version 2>&1 | awk '{print $2}')
        python_cmd="python"
    else
        python_version=$(python3 --version 2>&1 | awk '{print $2}')
        python_cmd="python3"
    fi
    
    if [ -z "$python_version" ]; then
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
    
    print_success "Python $python_version detected"
    
    # Extract major and minor version
    major=$(echo $python_version | cut -d. -f1)
    minor=$(echo $python_version | cut -d. -f2)
    
    if [ "$major" -eq 3 ] && [ "$minor" -ge 14 ]; then
        print_warning "Python $python_version detected. Some packages may not have wheels for this version."
        print_warning "Recommended: Use Python 3.8-3.12 for best compatibility"
        
        # Ask if user wants to continue
        echo ""
        print_message "Do you want to continue anyway? (y/n)"
        read -r continue_choice
        if [[ ! $continue_choice =~ ^[Yy]$ ]]; then
            print_message "Exiting. Please install Python 3.8-3.12 and try again."
            exit 0
        fi
    elif [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 8 ]); then
        print_warning "Python 3.8 or higher is recommended (you have $python_version)"
    else
        print_success "Python version is compatible"
    fi
    
    echo "$python_cmd"
}

# Install required packages
install_dependencies() {
    print_message "Installing required packages from requirements.txt..."
    
    # Upgrade pip, setuptools, and wheel first
    if check_windows; then
        python -m pip install --upgrade pip setuptools wheel
        python -m pip install --upgrade --force-reinstall packaging
    else
        python3 -m pip install --upgrade pip setuptools wheel
        python3 -m pip install --upgrade --force-reinstall packaging
    fi
    
    # Install requirements with fallback options
    if [ -f "requirements.txt" ]; then
        print_message "Attempting to install from requirements.txt..."
        
        if check_windows; then
            # Try normal install
            python -m pip install -r requirements.txt
            
            if [ $? -ne 0 ]; then
                print_warning "First attempt failed. Trying alternative installation method..."
                # Try installing one by one
                while IFS= read -r package; do
                    if [[ ! -z "$package" && ! "$package" =~ ^# ]]; then
                        print_message "Installing $package..."
                        python -m pip install --no-deps "$package" || true
                    fi
                done < requirements.txt
                # Then install dependencies
                python -m pip install -r requirements.txt --no-deps || true
            fi
        else
            python3 -m pip install -r requirements.txt
            
            if [ $? -ne 0 ]; then
                print_warning "First attempt failed. Trying alternative installation method..."
                # Try installing one by one
                while IFS= read -r package; do
                    if [[ ! -z "$package" && ! "$package" =~ ^# ]]; then
                        print_message "Installing $package..."
                        python3 -m pip install --no-deps "$package" || true
                    fi
                done < requirements.txt
                # Then install dependencies
                python3 -m pip install -r requirements.txt --no-deps || true
            fi
        fi
        
        # Final check
        print_message "Verifying installations..."
        if check_windows; then
            python -c "import streamlit; import pandas; print('Core packages installed successfully')" 2>/dev/null
        else
            python3 -c "import streamlit; import pandas; print('Core packages installed successfully')" 2>/dev/null
        fi
        
        if [ $? -eq 0 ]; then
            print_success "Core dependencies installed successfully"
        else
            print_warning "Some packages may have installation issues"
        fi
    else
        print_error "requirements.txt not found in current directory"
        exit 1
    fi
}

# Check if required files exist
check_files() {
    print_message "Checking required files..."
    
    missing_files=0
    
    # Check main Python files
    if [ ! -f "Chat_Analysiser_app.py" ]; then
        print_error "Chat_Analysiser_app.py not found"
        missing_files=$((missing_files + 1))
    fi
    
    if [ ! -f "Chat_Analysis.py" ]; then
        print_error "Chat_Analysis.py not found"
        missing_files=$((missing_files + 1))
    fi
    
    if [ ! -f "helper.py" ]; then
        print_error "helper.py not found"
        missing_files=$((missing_files + 1))
    fi
    
    # Check stop words file
    if [ ! -f "stop_hinglish.txt" ]; then
        print_warning "stop_hinglish.txt not found - will create a basic stop words file"
        create_stop_words_file
    else
        print_success "stop_hinglish.txt found"
    fi
    
    if [ $missing_files -eq 0 ]; then
        print_success "All required files found"
    else
        print_error "$missing_files required files are missing"
        exit 1
    fi
}

# Create stop words file
create_stop_words_file() {
    print_message "Creating default stop_hinglish.txt..."
    
    cat > stop_hinglish.txt << 'EOF'
the
a
an
and
or
but
in
on
at
to
for
of
with
by
from
up
about
into
through
during
before
after
is
are
was
were
be
been
being
have
has
had
do
does
did
will
would
shall
should
may
might
must
can
could
i
you
he
she
it
we
they
them
their
your
my
his
her
its
this
that
these
those
ka
ki
ke
ko
se
mein
par
aur
hai
hain
tha
the
thi
raha
rahe
rahi
kar
karke
karna
hoga
hoge
hogi
sakta
sakte
sakti
chahiye
apna
tum
aap
main
hum
yeh
woh
kya
kyun
kaise
kahan
kab
kitna
kitne
itna
utna
jab
tab
jahan
tahan
jaisa
aisa
waisa
maam
ma'am
sir
miss
mrs
mr
dr
prof
hello
hi
hey
ok
okay
thanks
thank
please
EOF
    print_success "Created default stop_hinglish.txt"
}

# Create directories if needed
create_directories() {
    print_message "Creating necessary directories..."
    
    # Create cache directory
    mkdir -p .cache
    
    # Create output directory for exports
    mkdir -p exports
    
    print_success "Directories created successfully"
}

# Test the installation
test_installation() {
    print_message "Testing installation..."
    
    if check_windows; then
        python -c "
import sys
print('Python version:', sys.version)
try:
    import streamlit
    print('✓ streamlit', streamlit.__version__)
except ImportError as e:
    print('✗ streamlit:', e)

try:
    import pandas
    print('✓ pandas', pandas.__version__)
except ImportError as e:
    print('✗ pandas:', e)

try:
    import numpy
    print('✓ numpy', numpy.__version__)
except ImportError as e:
    print('✗ numpy:', e)

try:
    import plotly
    print('✓ plotly', plotly.__version__)
except ImportError as e:
    print('✗ plotly:', e)

try:
    import emoji
    print('✓ emoji', emoji.__version__)
except ImportError as e:
    print('✗ emoji:', e)
" 2>&1
    else
        python3 -c "
import sys
print('Python version:', sys.version)
try:
    import streamlit
    print('✓ streamlit', streamlit.__version__)
except ImportError as e:
    print('✗ streamlit:', e)

try:
    import pandas
    print('✓ pandas', pandas.__version__)
except ImportError as e:
    print('✗ pandas:', e)

try:
    import numpy
    print('✓ numpy', numpy.__version__)
except ImportError as e:
    print('✗ numpy:', e)

try:
    import plotly
    print('✓ plotly', plotly.__version__)
except ImportError as e:
    print('✗ plotly:', e)

try:
    import emoji
    print('✓ emoji', emoji.__version__)
except ImportError as e:
    print('✗ emoji:', e)
" 2>&1
    fi
    
    echo ""
    if [ $? -eq 0 ]; then
        print_success "Import test completed"
    else
        print_warning "Some imports failed - there might be issues with some packages"
    fi
}

# Run the application
run_app() {
    print_message "Starting WhatsApp Chat Analyzer..."
    echo ""
    echo "========================================="
    echo "  Application will open in your browser  "
    echo "========================================="
    echo ""
    
    # Check if port is available (Linux/Mac only)
    if ! check_windows; then
        if command -v lsof &> /dev/null; then
            if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
                print_warning "Port 8501 is already in use. Attempting to use different port..."
                if check_windows; then
                    streamlit run Chat_Analysiser_app.py --server.port 8502
                else
                    streamlit run Chat_Analysiser_app.py --server.port 8502
                fi
            else
                if check_windows; then
                    streamlit run Chat_Analysiser_app.py
                else
                    streamlit run Chat_Analysiser_app.py
                fi
            fi
        else
            if check_windows; then
                streamlit run Chat_Analysiser_app.py
            else
                streamlit run Chat_Analysiser_app.py
            fi
        fi
    else
        if check_windows; then
            streamlit run Chat_Analysiser_app.py
        else
            streamlit run Chat_Analysiser_app.py
        fi
    fi
}

# Main execution
main() {
    echo ""
    print_message "Starting WhatsApp Chat Analyzer Setup..."
    echo ""
    
    # Check Python
    python_cmd=$(check_python)
    
    # Check required files
    check_files
    
    # Create virtual environment
    echo ""
    print_message "Do you want to create a virtual environment? (y/n)"
    read -r create_venv_choice
    
    if [[ $create_venv_choice =~ ^[Yy]$ ]]; then
        create_venv
    else
        print_message "Skipping virtual environment creation"
    fi
    
    # Install dependencies
    echo ""
    print_message "Do you want to install dependencies? (y/n)"
    read -r install_deps_choice
    
    if [[ $install_deps_choice =~ ^[Yy]$ ]]; then
        install_dependencies
    else
        print_message "Skipping dependency installation"
    fi
    
    # Create directories
    create_directories
    
    # Test installation
    test_installation
    
    # Ask to run app
    echo ""
    print_message "Do you want to run the WhatsApp Chat Analyzer now? (y/n)"
    read -r run_choice
    
    if [[ $run_choice =~ ^[Yy]$ ]]; then
        run_app
    else
        print_message "Setup complete! Run manually with: streamlit run Chat_Analysiser_app.py"
    fi
    
    echo ""
    print_success "Setup completed successfully!"
    echo ""
    print_message "If you created a virtual environment, activate it with:"
    if check_windows; then
        echo "  source venv/Scripts/activate"
    else
        echo "  source venv/bin/activate"
    fi
    echo ""
}

# Run main function
main
