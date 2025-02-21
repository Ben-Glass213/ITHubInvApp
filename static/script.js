document.addEventListener('DOMContentLoaded', function() {
    const registrationBtn = document.getElementById('registrationModeBtn');
    const lendingBtn = document.getElementById('lendingModeBtn');
    const registrationMode = document.getElementById('registrationMode');
    const lendingMode = document.getElementById('lendingMode');
  
    registrationBtn.addEventListener('click', function() {
      registrationMode.style.display = 'block';
      lendingMode.style.display = 'none';
    });
  
    lendingBtn.addEventListener('click', function() {
      lendingMode.style.display = 'block';
      registrationMode.style.display = 'none';
    });
  });
  