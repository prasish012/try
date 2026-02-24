<?php

$name = $email = $password = "";
$errors = [];
$success_message = "";

if ($_SERVER["REQUEST_METHOD"] === "POST") {

    $name = trim($_POST["name"] ?? "");
    $email = trim($_POST["email"] ?? "");
    $password = $_POST["password"] ?? ""; // Don't trim password
    $confirm_password = $_POST["confirm_password"] ?? ""; // Don't trim password

    if (empty($name)) {
        $errors['name'] = "Name is required.";
    }

    if (empty($email)) {
        $errors['email'] = "Email is required.";
    } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $errors['email'] = "Invalid email format.";
    }

    if (empty($password)) {
        $errors['password'] = "Password is required.";
    } elseif (strlen($password) < 6) {
        $errors['password'] = "At least 6 characters required.";
    } elseif (!preg_match('/[@#$%^&*!]/', $password)) {
        $errors['password'] = "Password must include a special character.";
    }

    if ($confirm_password !== $password) {
        $errors['confirm_password'] = "Passwords do not match.";
    }

    if (empty($errors)) {

        $json_file = "users.json";

        if (!file_exists($json_file)) {
            // Attempt to create the file if it doesn't exist
            if (file_put_contents($json_file, '[]') === false) {
                 $errors['file'] = "users.json file not found and could not be created.";
            } else {
                 $json_data = '[]';
            }
        } else {
            $json_data = file_get_contents($json_file);
        }
        
        if (empty($errors)) { // Check errors again after file creation attempt

            if ($json_data === false) {
                $errors['file'] = "Error reading users.json.";
            } else {

                $users = json_decode($json_data, true);

                if (!is_array($users)) {
                    $users = [];
                }

                foreach ($users as $user) {
                    if ($user["email"] === $email) {
                        $errors['email'] = "Email already registered.";
                        break;
                    }
                }

                if (empty($errors)) {

                    $hashed_password = password_hash($password, PASSWORD_DEFAULT);

                    $new_user = [
                        "name" => $name,
                        "email" => $email,
                        "password" => $hashed_password
                    ];

                    $users[] = $new_user;

                    $save = file_put_contents($json_file, json_encode($users, JSON_PRETTY_PRINT));

                    if ($save === false) {
                        $errors['file'] = "Error writing to users.json.";
                    } else {
                        $success_message = "Registration successful! You can now log in.";
                        // Clear successful data
                        $name = $email = $password = $confirm_password = "";
                    }
                }
            }
        }
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>User Registration</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">

    <style>
        body {
            font-family: 'Poppins', sans-serif;
            background: #eef1f5;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            color: #333;
        }

        .container {
            width: 380px;
            background: #ffffff;
            padding: 30px 35px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            border-radius: 12px;
        }

        h2 {
            text-align: center;
            margin-bottom: 25px;
            color: #1a1a1a;
            font-weight: 700;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            font-weight: 600;
            color: #555;
            display: block;
            margin-bottom: 5px;
        }

        input {
            width: 100%;
            padding: 12px;
            box-sizing: border-box;
            border: 1px solid #ddd;
            border-radius: 8px;
            outline: none;
            transition: border-color 0.3s, box-shadow 0.3s;
            font-size: 16px;
        }

        input:focus {
            border-color: #007bff;
            box-shadow: 0 0 5px rgba(0, 123, 255, 0.2);
        }

        button {
            width: 100%;
            background: #007bff;
            color: #fff;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 17px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
            margin-top: 10px;
        }

        button:hover {
            background: #0056b3;
        }

        .error {
            color: #dc3545;
            font-size: 14px;
            margin-top: 5px;
        }

        .success {
            background: #e6f7e6;
            color: #28a745;
            padding: 15px;
            text-align: center;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #c3e6c3;
            font-weight: 500;
        }
    </style>

</head>
<body>

<div class="container">

    <h2>Create Account</h2>

    <?php if (!empty($success_message)) : ?>
        <div class="success"><?= $success_message ?></div>
    <?php endif; ?>

    <form method="POST" action="">

        <div class="form-group">
            <label for="name">Name</label>
            <input type="text" id="name" name="name" value="<?= htmlspecialchars($name) ?>" placeholder="Enter your full name">
            <div class="error"><?= $errors['name'] ?? "" ?></div>
        </div>

        <div class="form-group">
            <label for="email">Email</label>
            <input type="email" id="email" name="email" value="<?= htmlspecialchars($email) ?>" placeholder="name@example.com">
            <div class="error"><?= $errors['email'] ?? "" ?></div>
        </div>

        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" placeholder="At least 6 characters & 1 special character">
            <div class="error"><?= $errors['password'] ?? "" ?></div>
        </div>

        <div class="form-group">
            <label for="confirm_password">Confirm Password</label>
            <input type="password" id="confirm_password" name="confirm_password" placeholder="Re-enter your password">
            <div class="error"><?= $errors['confirm_password'] ?? "" ?></div>
        </div>

        <button type="submit">Register</button>
        
        <div class="error" style="text-align: center; margin-top: 15px;"><?= $errors['file'] ?? "" ?></div>

    </form>
</div>

</body>
</html>