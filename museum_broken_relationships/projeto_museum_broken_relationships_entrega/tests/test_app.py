import os
import tempfile
import unittest
from datetime import UTC, datetime, timedelta

import models.game_model as game_model
from app import create_app


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        game_model.DB_PATH = os.path.join(self.temp_dir.name, 'test.db')
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret'})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def register(self):
        return self.client.post('/register', data={
            'username': 'utilizador_teste',
            'email': 'teste@example.com',
            'password': 'abcdef'
        })

    def finish_timer(self, field, slot_number=1):
        conn = game_model.get_db()
        conn.execute(
            f'UPDATE slot SET {field} = ? WHERE user_id = ? AND numero = ?',
            (
                (datetime.now(UTC) - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),
                1,
                slot_number
            )
        )
        conn.commit()
        conn.close()

    def test_api_requires_authentication(self):
        response = self.client.get('/api/estado')
        self.assertEqual(response.status_code, 401)

    def test_registration_creates_resources_and_slots(self):
        self.assertEqual(self.register().status_code, 302)
        state = self.client.get('/api/estado').get_json()
        self.assertEqual(state['amor_proprio'], 4)
        self.assertEqual(state['lagrimas'], 60)
        self.assertEqual(len(state['slots']), 4)

    def test_build_decision_and_collection_flow(self):
        self.register()
        build = self.client.post('/api/construir', json={'slot': 1})
        self.assertEqual(build.status_code, 200)
        self.assertEqual(build.get_json()['lagrimas'], 57)

        self.finish_timer('construcao_fim')
        self.client.post('/api/verificar_tarefa', json={'slot': 1})

        decision = self.client.post('/api/dar_ordem', json={
            'slot': 1,
            'tarefa_id': 'roupas',
            'opcao_id': 'B'
        })
        self.assertEqual(decision.status_code, 200)
        self.assertEqual(decision.get_json()['lagrimas'], 56)

        self.finish_timer('tarefa_fim')
        self.client.post('/api/verificar_tarefa', json={'slot': 1})
        collection = self.client.post('/api/recolher', json={'slot': 1})
        self.assertEqual(collection.status_code, 200)
        self.assertEqual(collection.get_json()['lagrimas'], 58)

    def test_invalid_json_is_rejected(self):
        self.register()
        response = self.client.post('/api/construir', data='invalid', content_type='text/plain')
        self.assertEqual(response.status_code, 400)

    def test_boolean_and_out_of_range_slots_are_rejected(self):
        self.register()
        self.assertEqual(self.client.post('/api/construir', json={'slot': True}).status_code, 400)
        self.assertEqual(self.client.post('/api/construir', json={'slot': 5}).status_code, 400)

    def test_registration_limits_are_validated_on_server(self):
        response = self.client.post('/register', data={
            'username': 'x' * 81,
            'email': 'teste@example.com',
            'password': 'abcdef'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('80 caracteres'.encode(), response.data)

    def test_registration_email_only_requires_at_sign(self):
        accepted = self.client.post('/register', data={
            'username': 'email_simples',
            'email': 'nome@dominio',
            'password': 'abcdef'
        })
        self.assertEqual(accepted.status_code, 302)

        self.client.get('/logout')
        rejected = self.client.post('/register', data={
            'username': 'email_invalido',
            'email': 'separador-em-falta',
            'password': 'abcdef'
        })
        self.assertEqual(rejected.status_code, 200)
        self.assertIn(b'O email deve conter @.', rejected.data)

    def test_login_and_logout(self):
        self.register()
        self.assertEqual(self.client.get('/logout').status_code, 302)
        login = self.client.post('/login', data={
            'username': 'utilizador_teste',
            'password': 'abcdef'
        })
        self.assertEqual(login.status_code, 302)
        self.assertEqual(self.client.get('/dashboard').status_code, 200)

    def test_decision_requires_tears(self):
        self.register()
        conn = game_model.get_db()
        conn.execute("UPDATE slot SET estado = 'ativo', etapa = 1 WHERE user_id = 1 AND numero = 1")
        conn.execute('UPDATE user SET lagrimas = 0 WHERE id = 1')
        conn.commit()
        conn.close()
        response = self.client.post('/api/dar_ordem', json={
            'slot': 1,
            'tarefa_id': 'roupas',
            'opcao_id': 'B'
        })
        self.assertEqual(response.status_code, 400)

    def test_restart_restores_initial_resources(self):
        self.register()
        conn = game_model.get_db()
        conn.execute('UPDATE user SET amor_proprio = 0, lagrimas = 2 WHERE id = 1')
        conn.commit()
        conn.close()
        self.assertEqual(self.client.post('/reiniciar').status_code, 302)
        state = self.client.get('/api/estado').get_json()
        self.assertEqual(state['amor_proprio'], 4)
        self.assertEqual(state['lagrimas'], 60)

    def test_restart_is_available_when_tears_reach_zero(self):
        self.register()
        conn = game_model.get_db()
        conn.execute('UPDATE user SET amor_proprio = 20, lagrimas = 0 WHERE id = 1')
        conn.commit()
        conn.close()
        self.assertEqual(self.client.post('/reiniciar').status_code, 302)
        state = self.client.get('/api/estado').get_json()
        self.assertEqual(state['lagrimas'], 60)

    def test_invalid_timer_is_recovered(self):
        self.register()
        conn = game_model.get_db()
        conn.execute(
            "UPDATE slot SET estado = 'processando', tarefa_fim = NULL WHERE user_id = 1 AND numero = 1"
        )
        conn.commit()
        conn.close()
        response = self.client.post('/api/verificar_tarefa', json={'slot': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['estado'], 'ativo')

    def test_corrupted_password_hash_does_not_crash_login(self):
        self.register()
        self.client.get('/logout')
        conn = game_model.get_db()
        conn.execute("UPDATE user SET password = 'hash-invalido' WHERE id = 1")
        conn.commit()
        conn.close()
        response = self.client.post('/login', data={
            'username': 'utilizador_teste',
            'password': 'abcdef'
        })
        self.assertEqual(response.status_code, 200)

    def test_bonus_task_persists_after_logout(self):
        self.register()
        conn = game_model.get_db()
        conn.execute("UPDATE slot SET estado = 'ativo', etapa = 3 WHERE user_id = 1 AND numero = 2")
        conn.commit()
        conn.close()

        decision = self.client.post('/api/dar_ordem', json={
            'slot': 2,
            'tarefa_id': 'redes',
            'opcao_id': 'B'
        })
        self.assertEqual(decision.status_code, 200)
        self.finish_timer('tarefa_fim', slot_number=2)
        self.client.post('/api/verificar_tarefa', json={'slot': 2})
        self.client.post('/api/recolher', json={'slot': 2})

        self.client.get('/logout')
        self.client.post('/login', data={
            'username': 'utilizador_teste',
            'password': 'abcdef'
        })
        bonus = self.client.post('/api/dar_ordem', json={
            'slot': 2,
            'tarefa_id': 'publicacoes',
            'opcao_id': 'A'
        })
        self.assertEqual(bonus.status_code, 200)

    def test_complete_game_reaches_final_state(self):
        self.register()
        task_plan = {
            1: [('roupas', 'B'), ('cartas', 'B'), ('presentes', 'B')],
            2: [('fotografias', 'B'), ('mensagens', 'B'), ('redes', 'B'), ('publicacoes', 'A')],
            3: [('pensamentos', 'B'), ('autocuidado', 'B'), ('amigos', 'B')],
            4: [('hobbies', 'B'), ('exercicio', 'B'), ('experiencias', 'B')],
        }

        for slot_number, tasks in task_plan.items():
            self.client.post('/api/construir', json={'slot': slot_number})
            self.finish_timer('construcao_fim', slot_number=slot_number)
            self.client.post('/api/verificar_tarefa', json={'slot': slot_number})

            for task_id, option_id in tasks:
                decision = self.client.post('/api/dar_ordem', json={
                    'slot': slot_number,
                    'tarefa_id': task_id,
                    'opcao_id': option_id
                })
                self.assertEqual(decision.status_code, 200)
                self.finish_timer('tarefa_fim', slot_number=slot_number)
                self.client.post('/api/verificar_tarefa', json={'slot': slot_number})
                collection = self.client.post('/api/recolher', json={'slot': slot_number})
                self.assertEqual(collection.status_code, 200)

        state = self.client.get('/api/estado').get_json()
        self.assertEqual(state['amor_proprio'], 100)
        self.assertTrue(all(slot['estado'] == 'finalizado' for slot in state['slots']))


if __name__ == '__main__':
    unittest.main()
