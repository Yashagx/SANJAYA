#Requires -RunAsAdministrator

# --- Configuration ---
$KeyFilePath = "C:\Users\Win11\OneDrive\Desktop\sanjaya-key.pem"
$Ec2User = "ec2-user"
$Ec2Ip = "18.61.252.222"
$ZipFileName = "sanjaya_auth_v2.zip"
$SourceDirectory = "sanjaya_auth_v2"

# --- Script ---

# 1. Check if the key file exists
if (-not (Test-Path $KeyFilePath)) {
    Write-Error "Deployment key not found at '$KeyFilePath'. Please update the path in the script."
    exit
}

# 2. Create the zip archive
Write-Host "Zipping the '$SourceDirectory' directory..."
if (Test-Path $ZipFileName) {
    Remove-Item $ZipFileName
}
Compress-Archive -Path $SourceDirectory -DestinationPath $ZipFileName
Write-Host "'$ZipFileName' created successfully."

# 3. Upload to EC2
Write-Host "Uploading '$ZipFileName' to $Ec2User@$Ec2Ip..."
scp -i $KeyFilePath $ZipFileName "$($Ec2User)@$($Ec2Ip):~/"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to upload the file to EC2. Please check your connection and permissions."
    exit
}
Write-Host "Upload complete."

# 4. Unzip & run deploy script on EC2
Write-Host "Connecting to EC2 to run deployment script..."
$SshCommand = "
unzip -o sanjaya_auth_v2.zip;
cd sanjaya_auth_v2;
chmod +x deploy.sh;
bash deploy.sh;
"
ssh -i $KeyFilePath "$($Ec2User)@$($Ec2Ip)" $SshCommand

if ($LASTEXITCODE -ne 0) {
    Write-Error "Deployment script failed on EC2. Connect via SSH to troubleshoot."
    exit
}

Write-Host "Deployment to EC2 completed successfully!"
Write-Host "The application should be running on port 8001."
Write-Host "Next step: Register your user via the web UI, then run 'python3 make_admin.py YOUR_USERNAME' on the server."

# 5. Clean up local zip file
Remove-Item $ZipFileName
