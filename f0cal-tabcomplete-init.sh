if ! grep -q "source $VIRTUAL_ENV/src/plugnparse/plugnparse/activate-argcomplete.sh" $VIRTUAL_ENV/bin/activate; then
  printf "\n\n# activates f0cal namespace tab completion
source $VIRTUAL_ENV/src/plugnparse/plugnparse/activate-argcomplete.sh" >> $VIRTUAL_ENV/bin/activate
fi
source $VIRTUAL_ENV/src/plugnparse/plugnparse/activate-argcomplete.sh