SetCompress off


Name "${PRODUCT_NAME}"
OutFile "${BUILD_DIR}\${PACKAGE_NAME}.exe"
InstallDir "${INSTDIR}"



Section "MainSection" SEC01
  SetOverwrite on
  SetOutPath "$INSTDIR"
  File  "${ARTIFACTS_DIR}\${PACKAGE_NAME}.msi"
SectionEnd

Section -PostInstall
      nsExec::Exec 'cmd /c C:\Windows\System32\msiexec.exe /qn /i "${INSTDIR}\${PACKAGE_NAME}.msi" /l*v "C:\Program Files\Scalarizr\var\log\nsis_to_msi_migration.log" '
SectionEnd
