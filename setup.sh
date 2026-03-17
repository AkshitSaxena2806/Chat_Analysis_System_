#!/bin/bash

# WhatsApp Chat Analyzer - Local Setup Script
echo "========================================="
echo "  WhatsApp Chat Analyzer - Setup Script  "
echo "========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p .cache exports

# Check for stop_hinglish.txt
if [ ! -f "stop_hinglish.txt" ]; then
    echo "Creating default stop_hinglish.txt..."
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
fi

echo ""
echo "Setup complete!"
echo "Run the app with: streamlit run Chat_Analysiser_app.py"
