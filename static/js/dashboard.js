    function toggleUpdateForm() {
        var updateForm = document.querySelector('.update-form');
        updateForm.style.display = updateForm.style.display === 'none' ? 'block' : 'none';
    }

    function toggleUpdateThoughtTextarea() {
        var updateThoughtTextarea = document.querySelector('.update-thought-textarea');
        updateThoughtTextarea.style.display = updateThoughtTextarea.style.display === 'none' ? 'block' : 'none';
    }
    // function toggleUpdateThoughtTextarea{{ loop.index }}() {
    //     var updateThoughtTextarea = document.querySelector('.update-thought-textarea-{{ loop.index }}');
    //     updateThoughtTextarea.style.display = updateThoughtTextarea.style.display === 'none' ? 'block' : 'none';
    // }

    function cancelUpdate() {
        var updateForms = document.querySelectorAll('.update-form');
        updateForms.forEach(function(form) {
            form.style.display = 'none';
        });
        var updateThoughtTextareas = document.querySelectorAll('.update-thought-textarea');
        updateThoughtTextareas.forEach(function(textarea) {
            textarea.style.display = 'none';
        });
    }
    function confirmDelete() {
        return confirm("Are you sure you want to delete this thought?");
    }

    // Function to trigger click event on hidden file input for uploading profile picture
function triggerProfilePictureUpload() {
    document.getElementById('profile_picture_upload').click();
}

// Function to handle file upload process for profile picture
document.getElementById('profile_picture_upload').addEventListener('change', function() {
    var file = this.files[0];
    if (file) {
        var reader = new FileReader();
        reader.onload = function(e) {
            // Display the uploaded image preview
            document.querySelector('.profile-picture').src = e.target.result;
            // Send AJAX request to save the image to MongoDB
            var formData = new FormData();
            formData.append('profile_picture', file);

            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload_profile_picture', true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    console.log('Image uploaded successfully.');
                } else {
                    console.error('Failed to upload image.');
                }
            };
            xhr.send(formData);
        };
        reader.readAsDataURL(file);
    }
});
// Function to trigger click event on hidden file input for uploading background picture
document.getElementById('uploadBackgroundImageButton').addEventListener('click', function() {
    document.getElementById('backgroundImageInput').click();
});
    
// Function to handle file upload process for backgroundImage
document.getElementById('backgroundImageInput').addEventListener('change', function() {
    var file = this.files[0];
    if (file) {
        var reader = new FileReader();
        reader.onload = function(e) {
            // Display the uploaded image preview
            // document.querySelector('.background-image').src = e.target.result;
            document.body.style.backgroundImage = 'url(' + e.target.result + ')';
            // Send AJAX request to save the image to MongoDB
            var formData = new FormData();
            formData.append('background_image', file);

            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload_background_image', true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    console.log('Background Image uploaded successfully.');
                } else {
                    console.error('Failed to upload image.');
                }
            };
            xhr.send(formData);
        };
        reader.readAsDataURL(file);
    }
});

    // // Function to trigger click event on hidden file input for uploading profile picture
    // function triggerProfilePictureUpload() {
    //     document.getElementById('profile_picture_upload').click();
    // }

    // // Function to handle file upload process for profile picture
    // document.getElementById('profile_picture_upload').addEventListener('change', function() {
    //     var file = this.files[0];
    //     if (file) {
    //         var reader = new FileReader();
    //         reader.onload = function(e) {
    //             // Display the uploaded image preview
    //             document.querySelector('.profile-picture').src = e.target.result;
    //             // Send AJAX request to save the image to MongoDB
    //         var formData = new FormData();
    //         formData.append('profile_picture', file);

    //         var xhr = new XMLHttpRequest();
    //         xhr.open('POST', '/upload_profile_picture', true);
    //         xhr.onload = function() {
    //             if (xhr.status === 200) {
    //                 console.log('Image uploaded successfully.');
    //             } else {
    //                 console.error('Failed to upload image.');
    //             }
    //         };
    //         xhr.send(formData);
    //         };
    //         reader.readAsDataURL(file);
    //     }
    // });
